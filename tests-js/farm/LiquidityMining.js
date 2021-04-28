const { expect } = require("chai");
const { expectRevert, expectEvent, constants, BN, balance, time } = require("@openzeppelin/test-helpers");
const { encodeParameters, etherMantissa, mineBlock, mineBlockNumber, increaseTime, blockNumber } = require("../Utils/Ethereum");

const { ZERO_ADDRESS } = constants;
const TOTAL_SUPPLY = etherMantissa(1000000000);

const TestToken = artifacts.require("TestToken");
const LiquidityMiningLogic = artifacts.require("LiquidityMiningMockup");
const LiquidityMiningProxy = artifacts.require("LiquidityMiningProxy");

contract("LiquidityMining", (accounts) => {
	const name = "Test SRV Token";
	const symbol = "TST";

	const rewardTokensPerBlock = new BN(3);
	const startDelayBlocks = new BN(1);
	const numberOfBonusBlocks = new BN(50);

	let root, account1, account2, account3, account4;
	let SRVToken, token1, token2, token3;
	let liquidityMining, wrapper;

	before(async () => {
		[root, account1, account2, account3, account4, ...accounts] = accounts;
	});

	beforeEach(async () => {
		SRVToken = await TestToken.new(name, symbol, 18, TOTAL_SUPPLY);
		token1 = await TestToken.new("Test token 1", "TST-1", 18, TOTAL_SUPPLY);
		token2 = await TestToken.new("Test token 2", "TST-2", 18, TOTAL_SUPPLY);
		token3 = await TestToken.new("Test token 3", "TST-3", 18, TOTAL_SUPPLY);
		wrapper = account1;

		await deployLiquidityMining();
		await liquidityMining.initialize(SRVToken.address, rewardTokensPerBlock, startDelayBlocks, numberOfBonusBlocks, wrapper);
	});

	describe("initialize", () => {
		it("sets the expected values", async () => {
			await deployLiquidityMining();
			let tx = await liquidityMining.initialize(SRVToken.address, rewardTokensPerBlock, startDelayBlocks, numberOfBonusBlocks, wrapper);

			let _SRV = await liquidityMining.SRV();
			let _rewardTokensPerBlock = await liquidityMining.rewardTokensPerBlock();
			let _startBlock = await liquidityMining.startBlock();
			let _bonusEndBlock = await liquidityMining.bonusEndBlock();
			let _wrapper = await liquidityMining.wrapper();

			let blockNumber = new BN(tx.receipt.blockNumber);

			expect(_SRV).equal(SRVToken.address);
			expect(_rewardTokensPerBlock).bignumber.equal(rewardTokensPerBlock);
			expect(_startBlock).bignumber.equal(startDelayBlocks.add(blockNumber));
			expect(_bonusEndBlock).bignumber.equal(startDelayBlocks.add(blockNumber).add(numberOfBonusBlocks));
			expect(_wrapper).equal(wrapper);
		});

		it("fails if not an owner", async () => {
			await deployLiquidityMining();
			await expectRevert(
				liquidityMining.initialize(SRVToken.address, rewardTokensPerBlock, startDelayBlocks, numberOfBonusBlocks, wrapper, {from: account1}),
				"unauthorized"
			);
		});

		it("fails if _startBlock = 0", async () => {
			await deployLiquidityMining();
			await expectRevert(
				liquidityMining.initialize(SRVToken.address, rewardTokensPerBlock, 0, numberOfBonusBlocks, wrapper),
				"Invalid start block"
			);
		});

		it("fails if already initialized", async () => {
			await expectRevert(
				liquidityMining.initialize(SRVToken.address, rewardTokensPerBlock, startDelayBlocks, numberOfBonusBlocks, wrapper),
				"Already initialized"
			);
		});

		it("fails if the 0 address is passed as token address", async () => {
			await deployLiquidityMining();
			await expectRevert(
				liquidityMining.initialize(ZERO_ADDRESS, rewardTokensPerBlock, startDelayBlocks, numberOfBonusBlocks, wrapper),
				"Invalid token address"
			);
		});
	});

	describe("setWrapper", () => {
		it("sets the expected values", async () => {
			let newWrapper = account2;
			await liquidityMining.setWrapper(newWrapper);

			let _wrapper = await liquidityMining.wrapper();
			expect(_wrapper).equal(newWrapper);
		});

		it("fails if not an owner", async () => {
			await expectRevert(
				liquidityMining.setWrapper(account2, {from: account1}),
				"unauthorized"
			);
		});
	});

	describe("stopMining", () => {
		it("should set end block", async () => {
			let tx = await liquidityMining.stopMining();

			let blockNumber = new BN(tx.receipt.blockNumber);
			let _endBlock = await liquidityMining.endBlock();
			expect(_endBlock).bignumber.equal(blockNumber);
		});

		it("fails if not an owner", async () => {
			await expectRevert(
				liquidityMining.stopMining({from: account1}),
				"unauthorized"
			);
		});

		it("fails if already stopped", async () => {
			await liquidityMining.stopMining();
			await expectRevert(
				liquidityMining.stopMining(),
				"Already stopped"
			);
		});
	});

	describe("transferSRV", () => {
		it("should be able to transfer SRV", async () => {
			let amount = new BN(1000);
			await SRVToken.transfer(liquidityMining.address, amount);

			let balanceBefore = await SRVToken.balanceOf(account1);
			await liquidityMining.transferSRV(account1, amount);
			let balanceAfter = await SRVToken.balanceOf(account1);

			expect(amount).bignumber.equal(balanceAfter.sub(balanceBefore));
		});

		it("only owner should be able to transfer", async () => {
			await expectRevert(liquidityMining.transferSRV(account1, 1000, { from: account1 }), "unauthorized");
		});

		it("fails if the 0 address is passed as receiver address", async () => {
			await expectRevert(liquidityMining.transferSRV(ZERO_ADDRESS, 1000), "receiver address invalid");
		});

		it("fails if the 0 is passed as an amount", async () => {
			await expectRevert(liquidityMining.transferSRV(account1, 0), "amount invalid");
		});
	});

	describe("add", () => {
		it("should be able to add pool token", async () => {
			let allocationPoint = new BN(1);
			let tx = await liquidityMining.add(token1.address, allocationPoint, false);

			expect(await liquidityMining.totalAllocationPoint()).bignumber.equal(allocationPoint);

			let poolInfo = await liquidityMining.poolInfoList(0);
			expect(poolInfo.poolToken).equal(token1.address);
			expect(poolInfo.allocationPoint).bignumber.equal(allocationPoint);
			let blockNumber = new BN(tx.receipt.blockNumber);
			expect(poolInfo.lastRewardBlock).bignumber.equal(blockNumber);
			expect(poolInfo.accumulatedRewardPerShare).bignumber.equal(new BN(0));

			expect(await liquidityMining.getPoolLength()).bignumber.equal(new BN(1));

			expectEvent(tx, "PoolTokenAdded", {
				user: root,
				poolToken: token1.address,
				allocationPoint: allocationPoint,
			});
		});

		it("should be able to add 2 pool tokens", async () => {
			let allocationPoint1 = new BN(1);
			let tx1 = await liquidityMining.add(token1.address, allocationPoint1, false);

			expect(await liquidityMining.totalAllocationPoint()).bignumber.equal(allocationPoint1);

			expectEvent(tx1, "PoolTokenAdded", {
				user: root,
				poolToken: token1.address,
				allocationPoint: allocationPoint1,
			});

			let allocationPoint2 = new BN(2);
			let tx2 = await liquidityMining.add(token2.address, allocationPoint2, false);

			expect(await liquidityMining.totalAllocationPoint()).bignumber.equal(allocationPoint1.add(allocationPoint2));

			expectEvent(tx2, "PoolTokenAdded", {
				user: root,
				poolToken: token2.address,
				allocationPoint: allocationPoint2,
			});
		});

		it("should be able to add pool token and update pools", async () => {
			//TODO implement
		});

		it("fails if the 0 allocation point is passed", async () => {
			await expectRevert(liquidityMining.add(token1.address, new BN(0), false), "Invalid allocation point");
		});

		it("fails if the 0 address is passed as token address", async () => {
			await expectRevert(liquidityMining.add(ZERO_ADDRESS, new BN(1), false), "Invalid token address");
		});

		it("fails if token already added", async () => {
			await liquidityMining.add(token1.address, new BN(1), false);
			await expectRevert(liquidityMining.add(token1.address, new BN(1), false), "Token already added");
		});
	});

	describe("update", () => {
		it("should be able to update pool token", async () => {
			let oldAllocationPoint = new BN(1);
			await liquidityMining.add(token1.address, oldAllocationPoint, false);

			let newAllocationPoint = new BN(2);
			let tx = await liquidityMining.update(token1.address, newAllocationPoint, false);

			expect(await liquidityMining.totalAllocationPoint()).bignumber.equal(newAllocationPoint);

			let poolInfo = await liquidityMining.getPoolInfo(token1.address);
			let blockNumber = new BN(tx.receipt.blockNumber);
			checkPoolInfo(poolInfo, token1.address, newAllocationPoint, blockNumber, new BN(0));

			expect(await liquidityMining.getPoolLength()).bignumber.equal(new BN(1));

			expectEvent(tx, "PoolTokenUpdated", {
				user: root,
				poolToken: token1.address,
				newAllocationPoint: newAllocationPoint,
				oldAllocationPoint: oldAllocationPoint,
			});
		});

		it("should be able to update pool token and update pools", async () => {
			//TODO implement
		});

		it("fails if token wasn't added", async () => {
			await expectRevert(liquidityMining.update(token1.address, new BN(1), false), "Pool token not found");
		});
	});

	describe("deposit", () => {
		let allocationPoint = new BN(1);
		let amount = new BN(1000);

		beforeEach(async () => {
			await liquidityMining.add(token1.address, allocationPoint, false);
			await mineBlocks(1);

			await token1.mint(account1, amount);
			await token1.approve(liquidityMining.address, amount, {from: account1});
		});

		it("should be able to deposit", async () => {
			let tx = await liquidityMining.deposit(token1.address, amount, ZERO_ADDRESS, {from: account1});

			let poolInfo = await liquidityMining.getPoolInfo(token1.address);
			let blockNumber = new BN(tx.receipt.blockNumber);
			checkPoolInfo(poolInfo, token1.address, allocationPoint, blockNumber, new BN(0));

			await checkUserPoolTokens(account1, token1, amount, amount, new BN(0));

			expectEvent(tx, "Deposit", {
				user: account1,
				poolToken: token1.address,
				amount: amount,
			});
		});

		it("should be able to deposit using wrapper", async () => {
			//TODO implement
		});

		it("fails if token pool token not found", async () => {
			await expectRevert(
				liquidityMining.deposit(account1, amount, ZERO_ADDRESS, {from: account1}),
				"Pool token not found"
			);
		});

	});

	describe("claimReward", () => {
		let allocationPoint = new BN(1);
		let amount = new BN(1000);

		beforeEach(async () => {
			await liquidityMining.add(token1.address, allocationPoint, false);
			await mineBlocks(1);

			await token1.mint(account1, amount);
			await token1.approve(liquidityMining.address, amount, {from: account1});
		});

		it("should be able to claim reward (will not be claimed without SRV tokens)", async () => {
			await liquidityMining.deposit(token1.address, amount, ZERO_ADDRESS, {from: account1});

			let tx = await liquidityMining.claimReward(token1.address, ZERO_ADDRESS, {from: account1});

			let poolInfo = await liquidityMining.getPoolInfo(token1.address);
			let blockNumber = new BN(tx.receipt.blockNumber);
			checkPoolInfo(poolInfo, token1.address, allocationPoint, blockNumber, new BN(-1));

			await checkUserPoolTokens(account1, token1, amount, amount, new BN(0));

			//user's balance of reward token
			let userRewardBalance = await SRVToken.balanceOf(account1);
			expect(userRewardBalance).bignumber.equal(new BN(0));
		});

		it("should be able to claim reward (will be claimed with SRV tokens)", async () => {
			let depositTx = await liquidityMining.deposit(token1.address, amount, ZERO_ADDRESS, {from: account1});
			let depositBlockNumber = new BN(depositTx.receipt.blockNumber);
			await SRVToken.transfer(liquidityMining.address, new BN(1000));

			let tx = await liquidityMining.claimReward(token1.address, ZERO_ADDRESS, {from: account1});

			let poolInfo = await liquidityMining.getPoolInfo(token1.address);
			let latestBlockNumber = new BN(tx.receipt.blockNumber);
			checkPoolInfo(poolInfo, token1.address, allocationPoint, latestBlockNumber, new BN(-1));

			await checkUserPoolTokens(account1, token1, amount, amount, new BN(0));
			let userReward = await checkUserReward(account1, token1, depositBlockNumber, latestBlockNumber);

			expectEvent(tx, "RewardClaimed", {
				user: account1,
				amount: userReward,
			});
		});

		it("should be able to claim reward using wrapper", async () => {
			//TODO implement
		});

		it("fails if token pool token not found", async () => {
			await expectRevert(liquidityMining.claimReward(account1, ZERO_ADDRESS, {from: account1}), "Pool token not found");
		});

	});

	describe("withdraw", () => {
		let allocationPoint = new BN(1);
		let amount = new BN(1000);

		beforeEach(async () => {
			await liquidityMining.add(token1.address, allocationPoint, false);
			await mineBlocks(1);

			await token1.mint(account1, amount);
			await token1.approve(liquidityMining.address, amount, {from: account1});
		});

		it("should be able to withdraw (without claiming reward)", async () => {
			await liquidityMining.deposit(token1.address, amount, ZERO_ADDRESS, {from: account1});

			let tx = await liquidityMining.withdraw(token1.address, amount, ZERO_ADDRESS, {from: account1});

			let poolInfo = await liquidityMining.getPoolInfo(token1.address);
			let blockNumber = new BN(tx.receipt.blockNumber);
			checkPoolInfo(poolInfo, token1.address, allocationPoint, blockNumber, new BN(-1));

			await checkUserPoolTokens(account1, token1, new BN(0), new BN(0), amount);

			//user's balance of reward token
			let userRewardBalance = await SRVToken.balanceOf(account1);
			expect(userRewardBalance).bignumber.equal(new BN(0));

			expectEvent(tx, "Withdraw", {
				user: account1,
				poolToken: token1.address,
				amount: amount,
			});
		});

		it("should be able to withdraw (with claiming reward)", async () => {
			let depositTx = await liquidityMining.deposit(token1.address, amount, ZERO_ADDRESS, {from: account1});
			let depositBlockNumber = new BN(depositTx.receipt.blockNumber);
			await SRVToken.transfer(liquidityMining.address, new BN(1000));

			let tx = await liquidityMining.withdraw(token1.address, amount, ZERO_ADDRESS, {from: account1});

			let poolInfo = await liquidityMining.getPoolInfo(token1.address);
			let latestBlockNumber = new BN(tx.receipt.blockNumber);
			checkPoolInfo(poolInfo, token1.address, allocationPoint, latestBlockNumber, new BN(-1));

			await checkUserPoolTokens(account1, token1, new BN(0), new BN(0), amount);
			let userReward = await checkUserReward(account1, token1, depositBlockNumber, latestBlockNumber);

			expectEvent(tx, "Withdraw", {
				user: account1,
				poolToken: token1.address,
				amount: amount,
			});

			expectEvent(tx, "RewardClaimed", {
				user: account1,
				amount: userReward,
			});
		});

		it("should be able to withdraw using wrapper", async () => {
			//TODO implement
		});

		it("fails if token pool token not found", async () => {
			await expectRevert(liquidityMining.withdraw(account1, amount, ZERO_ADDRESS, {from: account1}), "Pool token not found");
		});

		it("fails if token pool token not found", async () => {
			await expectRevert(liquidityMining.withdraw(token1.address, amount.mul(new BN(2)), ZERO_ADDRESS, {from: account1}), "Not enough balance");
		});

	});

	describe("emergencyWithdraw", () => {
		let allocationPoint = new BN(1);
		let amount = new BN(1000);

		beforeEach(async () => {
			await liquidityMining.add(token1.address, allocationPoint, false);
			await mineBlocks(1);

			await token1.mint(account1, amount);
			await token1.approve(liquidityMining.address, amount, {from: account1});
		});

		it("should be able to withdraw", async () => {
			await liquidityMining.deposit(token1.address, amount, ZERO_ADDRESS, {from: account1});

			let tx = await liquidityMining.emergencyWithdraw(token1.address, {from: account1});

			await checkUserPoolTokens(account1, token1, new BN(0), new BN(0), amount);

			let userInfo = await liquidityMining.getUserInfo(token1.address, account1);
			expect(userInfo.rewardDebt).bignumber.equal(new BN(0));
			expect(userInfo.accumulatedReward).bignumber.equal(new BN(0));

			expectEvent(tx, "EmergencyWithdraw", {
				user: account1,
				poolToken: token1.address,
				amount: amount,
			});
		});

		it("fails if token pool token not found", async () => {
			await expectRevert(liquidityMining.emergencyWithdraw(account1, {from: account1}), "Pool token not found");
		});

	});

	describe("getPassedBlocksWithBonusMultiplier", () => {

		it("check calculation", async () => {
			let bonusBlockMultiplier = await liquidityMining.BONUS_BLOCK_MULTIPLIER();
			let startBlock = await liquidityMining.startBlock();
			let bonusEndBlock = await liquidityMining.bonusEndBlock();
			let blocks;

			//[startBlock, bonusEndBlock]
			blocks = await liquidityMining.getPassedBlocksWithBonusMultiplier(startBlock, bonusEndBlock);
			expect(blocks).bignumber.equal(numberOfBonusBlocks.mul(bonusBlockMultiplier));

			//[startBlock - 100, bonusEndBlock]
			blocks = await liquidityMining.getPassedBlocksWithBonusMultiplier(startBlock.sub(new BN(100)), bonusEndBlock);
			expect(blocks).bignumber.equal(numberOfBonusBlocks.mul(bonusBlockMultiplier));

			//[startBlock, bonusEndBlock + 100]
			let blocksAfterBonusPeriod = new BN(100);
			blocks = await liquidityMining.getPassedBlocksWithBonusMultiplier(startBlock, bonusEndBlock.add(new BN(blocksAfterBonusPeriod)));
			expect(blocks).bignumber.equal(numberOfBonusBlocks.mul(bonusBlockMultiplier).add(blocksAfterBonusPeriod));

			//[startBlock, stopMining, ... bonusEndBlock]
			await mineBlocks(5);
			await liquidityMining.stopMining();
			let endBlock = await liquidityMining.endBlock();
			blocks = await liquidityMining.getPassedBlocksWithBonusMultiplier(startBlock, bonusEndBlock);
			expect(blocks).bignumber.equal(endBlock.sub(startBlock).mul(bonusBlockMultiplier));
		});

	});

	describe("getUserAccumulatedReward", () => {

		let amount1 = new BN(1000);
		let amount2 = new BN(2000);

		beforeEach(async () => {
			let allocationPoint1 = new BN(1);
			await liquidityMining.add(token1.address, allocationPoint1, false);

			let allocationPoint2 = new BN(2);
			await liquidityMining.add(token2.address, allocationPoint2, false);

			await mineBlock();

			await token1.mint(account1, amount1);
			await token1.approve(liquidityMining.address, amount1, {from: account1});
			await liquidityMining.deposit(token1.address, amount1, ZERO_ADDRESS, {from: account1});

			await token2.mint(account2, amount2);
			await token2.approve(liquidityMining.address, amount2, {from: account2});
			await liquidityMining.deposit(token2.address, amount2, ZERO_ADDRESS, {from: account2});

			await mineBlock();
		});

		it("check calculation", async () => {
			//TODO implement
			let reward1 = await liquidityMining.getUserAccumulatedReward(token1.address, account1);
			let reward2 = await liquidityMining.getUserAccumulatedReward(token2.address, account2);

		});

		//TODO add more tests

	});

	//TODO add tests for public/external getters

	async function deployLiquidityMining() {
		let liquidityMiningLogic = await LiquidityMiningLogic.new();
		let liquidityMiningProxy = await LiquidityMiningProxy.new();
		await liquidityMiningProxy.setImplementation(liquidityMiningLogic.address);
		liquidityMining = await LiquidityMiningLogic.at(liquidityMiningProxy.address);
	}

	async function mineBlocks(blocks) {
		for (let i = 0; i < blocks; i++) {
			await mineBlock();
		}
	}

	function checkPoolInfo(poolInfo, token, allocationPoint, lastRewardBlock, accumulatedRewardPerShare) {
		expect(poolInfo.poolToken).equal(token);
		expect(poolInfo.allocationPoint).bignumber.equal(allocationPoint);
		expect(poolInfo.lastRewardBlock).bignumber.equal(lastRewardBlock);
		if (accumulatedRewardPerShare.toNumber() !== -1) {
			expect(poolInfo.accumulatedRewardPerShare).bignumber.equal(accumulatedRewardPerShare);
		}
	}

	async function checkUserPoolTokens(user, poolToken, _userAmount, _liquidityMiningBalance, _userBalance) {
		//user balance in pool
		let userInfo = await liquidityMining.getUserInfo(poolToken.address, user);
		expect(userInfo.amount).bignumber.equal(_userAmount);
		//LM balance of pool tokens
		let liquidityMiningBalance = await poolToken.balanceOf(liquidityMining.address);
		expect(liquidityMiningBalance).bignumber.equal(_liquidityMiningBalance);
		//user's balance of pool tokens
		let userBalance = await poolToken.balanceOf(user);
		expect(userBalance).bignumber.equal(_userBalance);
	}

	//user's balance of reward token
	async function checkUserReward(user, poolToken, depositBlockNumber, latestBlockNumber) {
		let passedBlocks = await liquidityMining.getPassedBlocksWithBonusMultiplier(depositBlockNumber, latestBlockNumber);
		let userReward = passedBlocks.mul(rewardTokensPerBlock);
		let userRewardBalance = await SRVToken.balanceOf(user);
		expect(userRewardBalance).bignumber.equal(userReward);
		let userInfo = await liquidityMining.getUserInfo(poolToken.address, user);
		expect(userInfo.accumulatedReward).bignumber.equal(new BN(0));
		return userReward;
	}

});
