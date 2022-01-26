from os import access, lseek

from brownie.network import account
from scripts.helpful_scripts import get_account
from brownie import interface, network, config
from scripts.get_weth import get_weth
from web3 import Web3

amount = Web3.toWei(0.1, "ether")

def main(): 
    account = get_account()
    weth_token_address = config["networks"][network.show_active()]["weth-token"]
    dai_token_address =  config["networks"][network.show_active()]["dai_token"]

    if(network.show_active() in ["mainnet-fork"]):
        get_weth()
    #address and abi
    lending_pool = get_lending_pool()
   # print(lending_pool)
    deposited_eth, borrowable_eth , total_debt = get_borrowable_data(lending_pool, account.address)
    
    if(borrowable_eth < Web3.fromWei(amount, "ether")):
        #deposit weth to aave
        approve_erc20(lending_pool.address,amount, weth_token_address, account )
        tx = lending_pool.deposit( weth_token_address ,  amount, account.address, 0 ,{"from":account})
        tx.wait(1)
        print("Deposited!")
    
    print("let's borrow DAI!")
    get_borrowable_data(lending_pool, account.address)
    dai_eth_price = get_asset_price(config["networks"][network.show_active()]["dai_eth_price_feed"])
    #  1 dai = x eth, 
    #  ?dai = y eth  res: ?= y/x
    
    dai_amount_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    print(f"we are borrowing {dai_amount_to_borrow} DAI")
    # borrow() :- function borrow(address asset, uint256 amount, uint256 interestRateMode, uint16 referralCode, address onBehalfOf)
    br_tx = lending_pool.borrow(dai_token_address,  Web3.toWei(dai_amount_to_borrow,"ether"), 1, 0, account.address, {"from":account})
    br_tx.wait(1)
    print("Dai borrowed!")
    get_borrowable_data(lending_pool, account.address)
    print("repaying debts")
    #repay(): function repay(address asset, uint256 amount, uint256 rateMode, address onBehalfOf)
    approve_erc20(lending_pool.address,amount, weth_token_address, account )
    repay_tx = lending_pool.repay( dai_token_address, Web3.toWei(dai_amount_to_borrow,"ether") , 1, account.address, {"from":account})
    repay_tx.wait(1)
    get_borrowable_data(lending_pool, account.address)

    
def get_asset_price(address):
    dai_eth_price_feed = interface.AggregatorV3Interface(address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"The DAI/ETH price is {converted_latest_price}")
    return float(converted_latest_price)

def get_borrowable_data(lending_pool, address):
    (totalCollateralETH, totalDebtETH, availableBorrowsETH, currentLiquidationThreshold, ltv, healthFactor) = lending_pool.getUserAccountData(address)
    totalCollateralETH = Web3.fromWei(totalCollateralETH, "ether")
    totalDebtETH = Web3.fromWei(totalDebtETH, "ether")
    availableBorrowsETH = Web3.fromWei(availableBorrowsETH, "ether")
    print(f"you have {totalCollateralETH} worth of ETH deposited")
    print(f"you have {totalDebtETH} worth of ETH borrowed")
    print(f"you have {availableBorrowsETH} worth of ETH available to borrow")
    return (float(totalCollateralETH) ,float(availableBorrowsETH), float(totalDebtETH))



def get_lending_pool():
    #ABI 
    #Address 
    lending_pool_address = interface.ILendingPoolAddressesProvider(config["networks"][network.show_active()]["lending_pool_address_provider"]).getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool 

def approve_erc20(spender,amount, erc20_address,account):
    print("approving transaction")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from":account})
    tx.wait(1)
    return tx

