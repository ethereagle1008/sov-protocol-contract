/** Speed optimized on branch hardhatTestRefactor, 2021-10-01
 * Bottleneck found at beforeEach hook, redeploying tokens,
 *  protocol, ... on every test.
 *
 * Total time elapsed: 6.5s
 * After optimization: 5.3s
 *
 * Notes: Applied fixture to use snapshot beforeEach test.
 *   Moved some initialization code from tests to fixture.
 */

const { expect } = require("chai");
const { expectRevert, BN } = require("@openzeppelin/test-helpers");
const { waffle } = require("hardhat");
const { loadFixture } = waffle;

const LoanMaintenanceEvents = artifacts.require("LoanMaintenanceEvents");

const {
	getSUSD,
	getRBTC,
	getWRBTC,
	getBZRX,
	getLoanToken,
	getLoanTokenWRBTC,
	loan_pool_setup,
	set_demand_curve,
	lend_to_pool,
	getPriceFeeds,
	getSovryn,
	getSOV,
	decodeLogs,
	open_margin_trade_position,
} = require("../Utils/initializer.js");

// This decodes longs for a single event type, and returns a decoded object in
// the same form truffle-contract uses on its receipts

contract("ProtocolAddingMargin", (accounts) => {
	let owner;
	let sovryn, SUSD, WRBTC, RBTC, BZRX, loanToken, loanTokenWRBTC, priceFeeds;

	async function deploymentAndInitFixture(_wallets, _provider) {
		// Deploying sovrynProtocol w/ generic function from initializer.js
		SUSD = await getSUSD();
		RBTC = await getRBTC();
		WRBTC = await getWRBTC();
		BZRX = await getBZRX();
		priceFeeds = await getPriceFeeds(WRBTC, SUSD, RBTC, BZRX);

		sovryn = await getSovryn(WRBTC, SUSD, RBTC, priceFeeds);
		sov = await getSOV(sovryn, priceFeeds, SUSD, accounts);

		loanToken = await getLoanToken(owner, sovryn, WRBTC, SUSD);
		loanTokenWRBTC = await getLoanTokenWRBTC(owner, sovryn, WRBTC, SUSD);
		await loan_pool_setup(sovryn, owner, RBTC, WRBTC, SUSD, loanToken, loanTokenWRBTC);

		/// @dev Moved from some tests that require this initialization
		/// and is not interfering w/ any others.
		await set_demand_curve(loanToken);
		await lend_to_pool(loanToken, SUSD, owner);
	}

	before(async () => {
		[owner] = accounts;
	});

	beforeEach(async () => {
		await loadFixture(deploymentAndInitFixture);
	});

	describe("Adding Margin", () => {
		it("Test deposit collateral", async () => {
			// prepare the test
			const [loan_id] = await open_margin_trade_position(loanToken, RBTC, WRBTC, SUSD, owner);
			const loadData = await sovryn.getLoan(loan_id);
			const startCollateral = new BN(loadData["collateral"]);
			const deposit_amount = startCollateral.div(new BN(2));

			// deposit collateral to add margin to the loan created above
			await RBTC.approve(sovryn.address, deposit_amount);
			const { receipt } = await sovryn.depositCollateral(loan_id, deposit_amount);
			const { collateralToLoanRate } = await priceFeeds.getCurrentMargin(
				loadData["loanToken"],
				loadData["collateralToken"],
				loadData["principal"],
				loadData["collateral"]
			);
			const decode = decodeLogs(receipt.rawLogs, LoanMaintenanceEvents, "DepositCollateral");
			const args = decode[0].args;

			// verify the deposit collateral event

			expect(args["loanId"] == loan_id).to.be.true;
			expect(args["depositAmount"]).to.eq(deposit_amount.toString());
			expect(args["rate"]).to.eq(collateralToLoanRate.toString());

			// make sure, collateral was increased
			const endCollateral = (await sovryn.getLoan(loan_id))["collateral"];
			expect(new BN(endCollateral).sub(startCollateral).eq(deposit_amount)).to.be.true;
		});

		it("Test deposit collateral to non existent loan", async () => {
			// try to deposit collateral to a loan with id 0
			await RBTC.approve(sovryn.address, new BN(10).pow(new BN(15)));
			expectRevert(sovryn.depositCollateral("0x0", new BN(10).pow(new BN(15))), "loan is closed");
		});

		it("Test deposit collateral 0 value", async () => {
			// prepare the test
			const [loan_id] = await open_margin_trade_position(loanToken, RBTC, WRBTC, SUSD, owner);
			expectRevert(sovryn.depositCollateral(loan_id, new BN(0)), "depositAmount is 0");
		});
	});
});
