pragma solidity ^0.5.17;
pragma experimental ABIEncoderV2;

import "../../../openzeppelin/Ownable.sol";
import "../../../interfaces/IERC20.sol";
import "../../Staking/Staking.sol";
import "../../IFeeSharingProxy.sol";
import "../../ApprovalReceiver.sol";
import "./FourYearVestingStorage.sol";
import "../../../proxy/UpgradableProxy.sol";

/**
 * @title Four Year Vesting Contract.
 *
 * @notice A four year vesting contract.
 *
 * @dev Vesting contract is upgradable,
 * Make sure the vesting owner is multisig otherwise it will be
 * catastrophic.
 * */
contract FourYearVesting is FourYearVestingStorage, UpgradableProxy {
	/**
	 * @notice Setup the vesting schedule.
	 * @param _logic The address of logic contract.
	 * @param _SOV The SOV token address.
	 * @param _tokenOwner The owner of the tokens.
	 * @param _cliff The time interval to the first withdraw in seconds.
	 * @param _duration The total duration in seconds.
	 * @param _feeSharingProxy Fee sharing proxy address.
	 * */
	constructor(
		address _logic,
		address _SOV,
		address _stakingAddress,
		address _tokenOwner,
		uint256 _cliff,
		uint256 _duration,
		address _feeSharingProxy
	) public {
		require(_SOV != address(0), "SOV address invalid");
		require(_stakingAddress != address(0), "staking address invalid");
		require(_tokenOwner != address(0), "token owner address invalid");
		require(_cliff == 4 weeks, "invalid cliff");
		require(_duration == 156 weeks, "invalid duration");
		require(_feeSharingProxy != address(0), "feeSharingProxy address invalid");

		_setImplementation(_logic);
		SOV = IERC20(_SOV);
		staking = Staking(_stakingAddress);
		require(_duration <= staking.MAX_DURATION(), "duration may not exceed the max duration");
		tokenOwner = _tokenOwner;
		cliff = _cliff;
		duration = _duration;
		feeSharingProxy = IFeeSharingProxy(_feeSharingProxy);
		maxInterval = 18 * FOUR_WEEKS;
	}

	/**
	 * @dev We need to add this implementation to prevent proxy call
	 * FourYearVestingLogic.governanceWithdrawTokens.
	 * @param receiver The receiver of the token withdrawal.
	 * */
	function governanceWithdrawTokens(address receiver) public pure {
		revert("operation not supported");
	}

	/**
	 * @notice Set address of the implementation - vesting owner.
	 * @dev Overriding setImplementation function of UpgradableProxy. The logic can only be
	 * modified when both token owner and veting owner approve. Since
	 * setImplementation can only be called by vesting owner, we also need to check
	 * if the new logic is already approved by the token owner.
	 * @param _implementation Address of the implementation. Must match with what is set by token owner.
	 * */
	function setImplementation(address _implementation) public onlyProxyOwner {
		require(newImplementation != address(0), "invalid address");
		require(newImplementation == _implementation, "address mismatch");
		_setImplementation(_implementation);
		newImplementation = address(0);
	}
}
