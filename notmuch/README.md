## Deferred messages

The `handle-deferred` script implements support for deferring messages
in mutt.  With the example keybindings (`muttrc.deferred`) and crontab
(`crontab.deferred`) in place, selecting a message and typing `\dw`
(for example) will defer that message until the following Wednesday
(or, `\D` will defer a message until "later in the day").

Messages are deferred by adding the `archive` tag as well as a
specific `defer:*` tag (e.g., `defer:later` or `defer:wednesday`).

The `handle-deferred` will look for tagged messages and will remove
the `defer:*` and `archive` tags and add the `inbox` tag.

