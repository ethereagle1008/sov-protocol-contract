/** Speed optimized on branch hardhatTestRefactor, 2021-09-23
 * Bottlenecks found at beforeEach hook, redeploying token,
 *  protocol and loan on every test.
 *
 * Total time elapsed: 4.9s
 * After optimization: 4.5s
 *
 * Other minor optimizations:
 * - removed unneeded variables
 *
 * Notes: Applied fixture to use snapshot beforeEach test.
 */

const { assert } = require("chai");
const { waffle } = require("hardhat");
const { loadFixture } = waffle;
const { expectEvent, constants, ether } = require("@openzeppelin/test-helpers");

const TestToken = artifacts.require("TestToken");
const TestWrbtc = artifacts.require("TestWrbtc");

const sovrynProtocol = artifacts.require("sovrynProtocol");
const ProtocolSettings = artifacts.require("ProtocolSettings");
const ISovryn = artifacts.require("ISovryn");

const LoanToken = artifacts.require("LoanToken");
const LoanTokenLogicWrbtc = artifacts.require("LoanTokenLogicWrbtc");
const LoanSettings = artifacts.require("LoanSettings");
const LoanMaintenance = artifacts.require("LoanMaintenance");
const LoanOpenings = artifacts.require("LoanOpenings");
const LoanClosingsBase = artifacts.require("LoanClosingsBase");
const LoanClosingsWith = artifacts.require("LoanClosingsWith");
const SwapsExternal = artifacts.require("SwapsExternal");

const PriceFeedsLocal = artifacts.require("PriceFeedsLocal");
const TestSovrynSwap = artifacts.require("TestSovrynSwap");
const SwapsImplLocal = artifacts.require("SwapsImplLocal");

const TOTAL_SUPPLY = ether("1000");

contract("LoanSettingsEvents", (accounts) => {
	const name = "Test token";
	const symbol = "TST";

	let lender;
	let underlyingToken, testWrbtc;
	let sovryn, loanToken;
	let loanParams, loanParamsId, tx;

	async function deploymentAndInitFixture(_wallets, _provider) {
		// Token
		underlyingToken = await TestToken.new(name, symbol, 18, TOTAL_SUPPLY);
		testWrbtc = await TestWrbtc.new();

		const sovrynproxy = await sovrynProtocol.new();
		sovryn = await ISovryn.at(sovrynproxy.address);

		await sovryn.replaceContract((await LoanClosingsBase.new()).address);
		await sovryn.replaceContract((await LoanClosingsWith.new()).address);
		await sovryn.replaceContract((await ProtocolSettings.new()).address);
		await sovryn.replaceContract((await LoanSettings.new()).address);
		await sovryn.replaceContract((await LoanMaintenance.new()).address);
		await sovryn.replaceContract((await SwapsExternal.new()).address);
		await sovryn.replaceContract((await LoanOpenings.new()).address);

		await sovryn.setWrbtcToken(testWrbtc.address);

		feeds = await PriceFeedsLocal.new(testWrbtc.address, sovryn.address);
		await feeds.setRates(underlyingToken.address, testWrbtc.address, ether("0.01"));
		const swaps = await SwapsImplLocal.new();
		const sovrynSwapSimulator = await TestSovrynSwap.new(feeds.address);
		await sovryn.setSovrynSwapContractRegistryAddress(sovrynSwapSimulator.address);
		await sovryn.setSupportedTokens([underlyingToken.address, testWrbtc.address], [true, true]);
		await sovryn.setPriceFeedContract(
			feeds.address // priceFeeds
		);
		await sovryn.setSwapsImplContract(
			swaps.address // swapsImpl
		);
		await sovryn.setFeesController(lender);

		loanTokenLogicWrbtc = await LoanTokenLogicWrbtc.new();
		loanToken = await LoanToken.new(lender, loanTokenLogicWrbtc.address, sovryn.address, testWrbtc.address);
		await loanToken.initialize(testWrbtc.address, "iWRBTC", "iWRBTC"); // iToken
		loanToken = await LoanTokenLogicWrbtc.at(loanToken.address);

		const loanTokenAddress = await loanToken.loanTokenAddress();
		if (lender == (await sovryn.owner())) await sovryn.setLoanPool([loanToken.address], [loanTokenAddress]);

		await testWrbtc.mint(sovryn.address, ether("500"));

		loanParams = {
			id: "0x0000000000000000000000000000000000000000000000000000000000000000",
			active: false,
			owner: constants.ZERO_ADDRESS,
			loanToken: underlyingToken.address,
			collateralToken: testWrbtc.address,
			minInitialMargin: ether("50"),
			maintenanceMargin: ether("15"),
			maxLoanTerm: "2419200",
		};
	}

	before(async () => {
		[lender, ...accounts] = accounts;
	});

	beforeEach(async () => {
		await loadFixture(deploymentAndInitFixture);
	});

	describe("test LoanSettingsEvents", async () => {
		it("test setupLoanParamsEvents", async () => {
			tx = await sovryn.setupLoanParams([Object.values(loanParams)]);

			await expectEvent(tx, "LoanParamsIdSetup", { owner: lender });
			assert(tx.logs[1]["id"] != "0x0");

			await expectEvent(tx, "LoanParamsSetup", {
				owner: lender,
				loanToken: underlyingToken.address,
				collateralToken: testWrbtc.address,
				minInitialMargin: ether("50"),
				maintenanceMargin: ether("15"),
				maxLoanTerm: "2419200",
			});
			assert(tx.logs[0]["id"] != "0x0");
		});

		it("test disableLoanParamsEvents", async () => {
			tx = await sovryn.setupLoanParams([Object.values(loanParams)]);
			loanParamsId = tx.logs[1].args.id;

			tx = await sovryn.disableLoanParams([loanParamsId], { from: lender });

			await expectEvent(tx, "LoanParamsIdDisabled", { owner: lender });
			assert(tx.logs[1]["id"] != "0x0");

			await expectEvent(tx, "LoanParamsDisabled", {
				owner: lender,
				loanToken: underlyingToken.address,
				collateralToken: testWrbtc.address,
				minInitialMargin: ether("50"),
				maintenanceMargin: ether("15"),
				maxLoanTerm: "2419200",
			});
			assert(tx.logs[0]["id"] != "0x0");
		});
	});
});
