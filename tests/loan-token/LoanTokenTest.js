/** Speed optimized on branch hardhatTestRefactor, 2021-09-24
 * No bottlenecks found. The beforeEach hook deploys contracts but there is only one test.
 *
 * Total time elapsed: 4.1s
 *
 * Other minor optimizations:
 * - removed unneeded variables
 *
 * Notes:
 *   Updated to use the initializer.js functions for protocol deployment.
 *   Updated to use SUSD as underlying token, instead of custom underlyingToken.
 */

const { constants } = require("@openzeppelin/test-helpers");
const {
	getSUSD,
	getRBTC,
	getWRBTC,
	getBZRX,
	getLoanTokenLogic,
	getLoanToken,
	getLoanTokenLogicWrbtc,
	getLoanTokenWRBTC,
	loan_pool_setup,
	set_demand_curve,
	getPriceFeeds,
	getSovryn,
	decodeLogs,
	getSOV,
} = require("../Utils/initializer.js");

const GovernorAlpha = artifacts.require("GovernorAlphaMockup");
const Timelock = artifacts.require("TimelockHarness");
const StakingLogic = artifacts.require("Staking");
const StakingProxy = artifacts.require("StakingProxy");

const LoanTokenSettings = artifacts.require("LoanTokenSettingsLowerAdmin");

const PreviousLoanTokenSettings = artifacts.require("PreviousLoanTokenSettingsLowerAdmin");
const PreviousLoanToken = artifacts.require("PreviousLoanToken");

const TWO_DAYS = 86400 * 2;

contract("LoanTokenUpgrade", (accounts) => {
	let root;
	let SUSD, staking, gov, timelock;
	let loanTokenSettings, sovryn, loanToken;

	before(async () => {
		[root, ...accounts] = accounts;
	});

	/// @dev In case more tests were being added to this file,
	///   the beforeEach hook should be calling a fixture
	///   to avoid repeated deployments.
	beforeEach(async () => {
		// Deploying sovrynProtocol w/ generic function from initializer.js
		SUSD = await getSUSD();
		RBTC = await getRBTC();
		WRBTC = await getWRBTC();
		BZRX = await getBZRX();
		priceFeeds = await getPriceFeeds(WRBTC, SUSD, RBTC, BZRX);
		sovryn = await getSovryn(WRBTC, SUSD, RBTC, priceFeeds);
		await sovryn.setSovrynProtocolAddress(sovryn.address);

		// Staking
		let stakingLogic = await StakingLogic.new(SUSD.address);
		staking = await StakingProxy.new(SUSD.address);
		await staking.setImplementation(stakingLogic.address);
		staking = await StakingLogic.at(staking.address);

		// Governor
		timelock = await Timelock.new(root, TWO_DAYS);
		gov = await GovernorAlpha.new(timelock.address, staking.address, root, 4, 0);
		await timelock.harnessSetAdmin(gov.address);

		// Settings
		loanTokenSettings = await PreviousLoanTokenSettings.new();
		loanToken = await PreviousLoanToken.new(root, loanTokenSettings.address, loanTokenSettings.address, SUSD.address);
		loanToken = await PreviousLoanTokenSettings.at(loanToken.address);

		await sovryn.transferOwnership(timelock.address);
	});

	describe("change settings", () => {
		it("admin field should be readable", async () => {
			let previousSovrynContractAddress = await loanToken.sovrynContractAddress();
			let previousWrbtcTokenAddress = await loanToken.wrbtcTokenAddress();

			let newLoanTokenSettings = await LoanTokenSettings.new();

			let loanTokenProxy = await PreviousLoanToken.at(loanToken.address);
			await loanTokenProxy.setTarget(newLoanTokenSettings.address);

			loanToken = await LoanTokenSettings.at(loanToken.address);

			// check that previous admin is address(0)
			let admin = await loanToken.admin();
			assert.equal(admin, constants.ZERO_ADDRESS);

			// await expectRevert(loanToken.changeLoanTokenNameAndSymbol("newName", "newSymbol", { from: account1 }), "unauthorized");

			// change admin
			await loanToken.setAdmin(root);

			admin = await loanToken.admin();
			assert.equal(admin, root);

			// await loanToken.changeLoanTokenNameAndSymbol("newName", "newSymbol");

			let sovrynContractAddress = await loanToken.sovrynContractAddress();
			let wrbtcTokenAddress = await loanToken.wrbtcTokenAddress();

			assert.equal(sovrynContractAddress, previousSovrynContractAddress);
			assert.equal(wrbtcTokenAddress, previousWrbtcTokenAddress);
		});
	});
});
