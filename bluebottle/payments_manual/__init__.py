"""
Manual payments module to resolve unmatched bank transactions or other issues.

When a user donates money for a project/fundraiser/... directly to the bank
account (bypassing the website), this donation needs to be entered manually.
To avoid losing a certain percentage/amount to docdata, we need to skip the
regular payment flow and perform it 'behind the curtains'.

A manual order will be created, with the user set to the user resolving the
donation, and it will be marked anonymous. Afterwards, the donation/order can be
set to the correct user - if it exists on the website, and be de-anonymized so
the donation shows up properly on the front end.

To summarize, the big advantage is that no manual payment has to be performed
from the 1% account, and no fees will be deducted since the donation was done
around docdata. This manual payment will not exists at all in DocData.

The ManualPayment model is another Polymorphic Payment model.
"""
