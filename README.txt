mc-stock

Checks stock for a list of given items at specified Microcenter location,
and notifies the user via email.

To run mc-stock, instantiate a Clerk with a list of urls,
or create a Store object for more granular control.

A store number is required to get accurate stock numbers.
The default store number is set to the North Dallas/Richardson, TX location.

Also required is valid email account information for notifications.
If a recipient address is not provided, the user will be prompted for one.
If the prompt is empty, notifications are sent from the sender
address to itself.  Providing an empty string for recipient is a valid
argument to enable loopback operation, as only a value of None
will trigger a prompt.

The default time between checks is 15 minutes.  This value should
be at least a few minutes, to avoid being blacklisted by the
server, though this class enforces no such limit.  To change the
time period, provide a value in minutes to self.run(minutes).

Setting debug to True enables false positives for testing.
