from api import *


print("Starting test of xcat...")
htlcTrade = initiate()
buyer_fulfill(htlcTrade)
# zXcat.generate(8)

# print("LLLLTTTTTTTTTTTTT:: ",zXcat.zcashd.listtransactions())
zXcat.generate(2)
redeem_seller(htlcTrade)
zXcat.generate(2)

redeem_buyer(htlcTrade)


# addr = CBitcoinAddress('tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ')
# print(addr)
# # print(b2x('tmFRXyju7ANM7A9mg75ZjyhFW1UJEhUPwfQ'))
# print(b2x(addr))
