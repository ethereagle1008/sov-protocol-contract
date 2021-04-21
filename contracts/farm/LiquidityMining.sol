pragma solidity 0.5.17;
pragma experimental ABIEncoderV2;

/// SPDX-License-Identifier: MIT

import "../openzeppelin/ERC20.sol";
import "../openzeppelin/SafeERC20.sol";
import "../openzeppelin/SafeMath.sol";
import "./Upgradeable.sol";



// MasterChef is the master of RSOV. He can make RSOV and he is a fair guy.
//
// Note that it's ownable and the owner wields tremendous power. The ownership
// will be transferred to a governance smart contract once RSOV is sufficiently
// distributed and the community can show to govern itself.
//
// Have fun reading it. Hopefully it's bug-free. God bless.
contract LiquidityMining is Upgradeable {
    using SafeMath for uint256;
    using SafeERC20 for IERC20;

    // Info of each user.
    struct UserInfo {
        uint256 amount; // How many LP tokens the user has provided.
        uint256 rewardDebt; // Reward debt. See explanation below.
        //
        // We do some fancy math here. Basically, any point in time, the amount of RSOVs
        // entitled to a user but is pending to be distributed is:
        //
        //   pending reward = (user.amount * pool.accRSOVPerShare) - user.rewardDebt
        //
        // Whenever a user deposits or withdraws LP tokens to a pool. Here's what happens:
        //   1. The pool's `accRSOVPerShare` (and `lastRewardBlock`) gets updated.
        //   2. User receives the pending reward sent to his/her address.
        //   3. User's `amount` gets updated.
        //   4. User's `rewardDebt` gets updated.
    }
    // Info of each pool.
    struct PoolInfo {
        IERC20 lpToken; // Address of LP token contract.
        uint256 allocPoint; // How many allocation points assigned to this pool. RSOVs to distribute per block.
        uint256 lastRewardBlock; // Last block number that RSOVs distribution occurs.
        uint256 accRSOVPerShare; // Accumulated RSOVs per share, times 1e12. See below.
    }
    // The RSOV TOKEN!
    ERC20 public RSOV;
    // Dev address.
    address public devaddr;
    // Block number when bonus RSOV period ends.
    uint256 public bonusEndBlock;
    // RSOV tokens created per block.
    uint256 public RSOVPerBlock;
    // Bonus muliplier for early RSOV makers.
    uint256 public constant BONUS_MULTIPLIER = 10;
    // Info of each pool.
    PoolInfo[] public poolInfo;
    // Info of each user that stakes LP tokens.
    mapping(uint256 => mapping(address => UserInfo)) public userInfo;
    // Total allocation poitns. Must be the sum of all allocation points in all pools.
    uint256 public totalAllocPoint = 0;
    // The block number when RSOV mining starts.
    uint256 public startBlock;
    event Deposit(address indexed user, uint256 indexed pid, uint256 amount);
    event Withdraw(address indexed user, uint256 indexed pid, uint256 amount);
    event EmergencyWithdraw(
        address indexed user,
        uint256 indexed pid,
        uint256 amount
    );

    function initialize(
        ERC20 _RSOV,
        address _devaddr,
        uint256 _RSOVPerBlock,
        uint256 _startBlock,
        uint256 _bonusEndBlock
    ) public onlyOwner {
        require(address(RSOV) == address(0), "unauthorized");
        RSOV = _RSOV;
        devaddr = _devaddr;
        RSOVPerBlock = _RSOVPerBlock;
        bonusEndBlock = _bonusEndBlock;
        startBlock = _startBlock;
    }

    function poolLength() external view returns (uint256) {
        return poolInfo.length;
    }

    // Add a new lp to the pool. Can only be called by the owner.
    // XXX DO NOT add the same LP token more than once. Rewards will be messed up if you do.
    function add(
        uint256 _allocPoint,
        IERC20 _lpToken,
        bool _withUpdate
    ) public onlyOwner {
        if (_withUpdate) {
            massUpdatePools();
        }
        uint256 lastRewardBlock =
            block.number > startBlock ? block.number : startBlock;
        totalAllocPoint = totalAllocPoint.add(_allocPoint);
        poolInfo.push(
            PoolInfo({
                lpToken: _lpToken,
                allocPoint: _allocPoint,
                lastRewardBlock: lastRewardBlock,
                accRSOVPerShare: 0
            })
        );
    }

    // Update the given pool's RSOV allocation point. Can only be called by the owner.
    function set(
        uint256 _pid,
        uint256 _allocPoint,
        bool _withUpdate
    ) public onlyOwner {
        if (_withUpdate) {
            massUpdatePools();
        }
        totalAllocPoint = totalAllocPoint.sub(poolInfo[_pid].allocPoint).add(
            _allocPoint
        );
        poolInfo[_pid].allocPoint = _allocPoint;
    }


    // Return reward multiplier over the given _from to _to block.
    function getMultiplier(uint256 _from, uint256 _to)
        public
        view
        returns (uint256)
    {
        if (_to <= bonusEndBlock) {
            return _to.sub(_from).mul(BONUS_MULTIPLIER);
        } else if (_from >= bonusEndBlock) {
            return _to.sub(_from);
        } else {
            return
                bonusEndBlock.sub(_from).mul(BONUS_MULTIPLIER).add(
                    _to.sub(bonusEndBlock)
                );
        }
    }

    
    function _pendingRSOV(uint256 _pid, address _user)
        internal
        view
        returns (uint256)
    {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][_user];
        uint256 accRSOVPerShare = pool.accRSOVPerShare;
        uint256 lpSupply = pool.lpToken.balanceOf(address(this));
        if (block.number > pool.lastRewardBlock && lpSupply != 0) {
            uint256 multiplier =
                getMultiplier(pool.lastRewardBlock, block.number);
            uint256 RSOVReward =
                multiplier.mul(RSOVPerBlock).mul(pool.allocPoint).div(
                    totalAllocPoint
                );
            accRSOVPerShare = accRSOVPerShare.add(
                RSOVReward.mul(1e12).div(lpSupply)
            );
        }
        return user.amount.mul(accRSOVPerShare).div(1e12).sub(user.rewardDebt);
    }


    // View function to see pending RSOVs on frontend.
    function pendingRSOV(uint256 _pid, address _user)
        external
        view
        returns (uint256)
    {
        return _pendingRSOV(_pid, _user);
    }


    // Update reward vairables for all pools. Be careful of gas spending!
    function massUpdatePools() public {
        uint256 length = poolInfo.length;
        for (uint256 pid = 0; pid < length; ++pid) {
            updatePool(pid);
        }
    }

    // Update reward variables of the given pool to be up-to-date.
    function updatePool(uint256 _pid) public {
        PoolInfo storage pool = poolInfo[_pid];
        if (block.number <= pool.lastRewardBlock) {
            return;
        }
        uint256 lpSupply = pool.lpToken.balanceOf(address(this));
        if (lpSupply == 0) {
            pool.lastRewardBlock = block.number;
            return;
        }
        uint256 multiplier = getMultiplier(pool.lastRewardBlock, block.number);
        uint256 RSOVReward =
            multiplier.mul(RSOVPerBlock).mul(pool.allocPoint).div(
                totalAllocPoint
            );
        //todo original code minted tokens here, we have to supply tokens to this contract instead
        //RSOV.mint(devaddr, RSOVReward.div(10));
        //RSOV.mint(address(this), RSOVReward);
        pool.accRSOVPerShare = pool.accRSOVPerShare.add(
            RSOVReward.mul(1e12).div(lpSupply)
        );
        pool.lastRewardBlock = block.number;
    }

    // Deposit LP tokens to MasterChef for RSOV allocation.
    function deposit(uint256 _pid, uint256 _amount) public {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        updatePool(_pid);
        if (user.amount > 0) {
            uint256 pending =
                user.amount.mul(pool.accRSOVPerShare).div(1e12).sub(
                    user.rewardDebt
                );
            safeRSOVTransfer(msg.sender, pending);
        }
        pool.lpToken.safeTransferFrom(
            address(msg.sender),
            address(this),
            _amount
        );
        user.amount = user.amount.add(_amount);
        user.rewardDebt = user.amount.mul(pool.accRSOVPerShare).div(1e12);
        emit Deposit(msg.sender, _pid, _amount);
    }

    function claimReward(uint256 _pid) public {
        deposit(_pid, 0);
    }

    // Withdraw LP tokens from MasterChef.
    function withdraw(uint256 _pid, uint256 _amount) public {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        require(user.amount >= _amount, "withdraw: not good");
        updatePool(_pid);
        uint256 pending =
            user.amount.mul(pool.accRSOVPerShare).div(1e12).sub(
                user.rewardDebt
            );
        safeRSOVTransfer(msg.sender, pending);
        user.amount = user.amount.sub(_amount);
        user.rewardDebt = user.amount.mul(pool.accRSOVPerShare).div(1e12);
        pool.lpToken.safeTransfer(address(msg.sender), _amount);
        emit Withdraw(msg.sender, _pid, _amount);
    }

    // Withdraw without caring about rewards. EMERGENCY ONLY.
    function emergencyWithdraw(uint256 _pid) public {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][msg.sender];
        pool.lpToken.safeTransfer(address(msg.sender), user.amount);
        emit EmergencyWithdraw(msg.sender, _pid, user.amount);
        user.amount = 0;
        user.rewardDebt = 0;
    }

    // Safe RSOV transfer function, just in case if rounding error causes pool to not have enough RSOVs.
    function safeRSOVTransfer(address _to, uint256 _amount) internal {
        uint256 RSOVBal = RSOV.balanceOf(address(this));
        if (_amount > RSOVBal) {
            RSOV.transfer(_to, RSOVBal);
        } else {
            RSOV.transfer(_to, _amount);
        }
    }

    // Update dev address by the previous dev.
    function dev(address _devaddr) public {
        require(msg.sender == devaddr, "dev: wut?");
        devaddr = _devaddr;
    }


    // Custom logic - helpers


    function getPoolInfos() external view returns(PoolInfo[] memory poolInfos){
        uint256 length = poolInfo.length;
        poolInfos = new PoolInfo[](length);
        for (uint256 pid = 0; pid < length; ++pid) {
            poolInfos[pid] = poolInfo[pid];
        }
    }

    function getOptimisedUserInfos(address _user) external view returns(uint256[2][] memory userInfos){
        uint256 length = poolInfo.length;
        userInfos = new uint256[2][](length);
        for (uint256 pid = 0; pid < length; ++pid) {
            userInfos[pid][0] = userInfo[pid][_user].amount;
            userInfos[pid][1] = _pendingRSOV(pid, _user);

        }
    }

    function getUserInfos(address _wallet) external view returns(UserInfo[] memory userInfos){
        uint256 length = poolInfo.length;
        userInfos = new UserInfo[](length);
        for (uint256 pid = 0; pid < length; ++pid) {
            userInfos[pid] = userInfo[pid][_wallet];
        }
    }

    function getPendingRSOV(address _user) external view returns(uint256[] memory pending){
        uint256 length = poolInfo.length;
        pending = new uint256[](length);
        for (uint256 pid = 0; pid < length; ++pid) {
            pending[pid] = _pendingRSOV(pid, _user);
        }
    }

}