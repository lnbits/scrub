<a href="https://lnbits.com" target="_blank" rel="noopener noreferrer">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://i.imgur.com/QE6SIrs.png">
    <img src="https://i.imgur.com/fyKPgVT.png" alt="LNbits" style="width:280px">
  </picture>
</a>

[![License: MIT](https://img.shields.io/badge/License-MIT-success?logo=open-source-initiative&logoColor=white)](./LICENSE)
[![Built for LNbits](https://img.shields.io/badge/Built%20for-LNbits-4D4DFF?logo=lightning&logoColor=white)](https://github.com/lnbits/lnbits)

# Scrub - <small>[LNbits](https://github.com/lnbits/lnbits) extension</small>

<small>For more about LNBits extension check [this tutorial](https://github.com/lnbits/lnbits/wiki/LNbits-Extensions)</small>

## Automatically forward funds (Scrub) that get paid to the wallet to an LNURLpay or Lightning Address

SCRUB is a small but handy extension that allows a user to take advantage of all the functionalities inside **LNbits** and upon a payment received to your LNbits wallet, automatically forward it to your desired wallet via LNURL or LNAddress!

<small>Only whole values, integers, are Scrubbed, amounts will be rounded down (example: 6.3 will be 6)! The decimals, if existing, will be kept in your wallet!</small>

[**Wallets supporting LNURL**](https://github.com/fiatjaf/awesome-lnurl#wallets)

## Usage

1. Create an scrub (New Scrub link)\
   ![create scrub](https://i.imgur.com/LUeNkzM.jpg)

   - select the wallet to be _scrubbed_
   - make a small description
   - enter either an LNURL pay or a lightning address

   Make sure your LNURL or LNaddress is correct!

2. A new scrub will show on the _Scrub links_ section\
   ![scrub](https://i.imgur.com/LNoFkeu.jpg)

   - only one scrub can be created for each wallet!
   - You can _edit_ or _delete_ the Scrub at any time\
     ![edit scrub](https://i.imgur.com/Qu65lGG.jpg)

3. On your wallet, you'll see a transaction of a payment received and another right after it as apayment sent, marked with **#scrubed**\
   ![wallet view](https://i.imgur.com/S6EWWCP.jpg)

## Powered by LNbits

[LNbits](https://lnbits.com) is a free and open-source lightning accounts system.

[![Visit LNbits Shop](https://img.shields.io/badge/Visit-LNbits%20Shop-7C3AED?logo=shopping-cart&logoColor=white&labelColor=5B21B6)](https://shop.lnbits.com/)
[![Try myLNbits SaaS](https://img.shields.io/badge/Try-myLNbits%20SaaS-2563EB?logo=lightning&logoColor=white&labelColor=1E40AF)](https://my.lnbits.com/login)
