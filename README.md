Fenestra
========

(Latin for "window")

Fenestra is a tool for setting up a windowing environment. Specifically, at the moment it builds my very specific i3+polybar+supervisor config.
It's however semi-generalisable, and could probably be refactored to not be entirely locked to my config, but I haven't gotten around to looking
at that yet. It responds to events (USB changes, screen changes, network interface changes) to decide to reconfigure things (e.g. changing screen layouts).

It uses [Supervisor](http://supervisord.org/) as a session manager (as i3 doesn't really have one natively).