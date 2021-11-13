wekan-db
========

As of 11/2021, Wekan does not provide a way to [move a list to a different
board][1] or to [move multiple cards to a list on a different board][2], nor
does [the API][3] seem to support this. 

[1]: https://github.com/wekan/wekan/issues/3531
[2]: https://github.com/wekan/wekan/issues/2155
[3]: https://wekan.github.io/api/v2.55/#wekan-rest-api

This tool remedies this by manipulating the Wekan database directly.

It has been tested with Wekan 5.75.0. It might break if Wekan chooses to change
the database schema.

Manipulating the database directly is risky. Be aware of the risks and make
backups.


Usage
-----

Basic usage (example):

    wekan-db.py "General" "TODO" "Projects" "Open"

This moves all cards from list `todo` on board `General` to list `Open` on board
`Projects`.

If there are multiple lists source lists with the same name, you need to specify
`--merge-source`. If there are already cards in the target list, you need to
specify `--merge-target`.

More information is available in the online help:

    wekan-db.py --help


Limitations
-----------

The user ID is not considered. If multiple users have a board and list with the
same name, cards from all of them may be move to the same target board.
