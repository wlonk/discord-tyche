=====
Tyche
=====

The goddess of fortune.

A discord bot for Transneptune.

Skills
------

Dicerolling
~~~~~~~~~~~

``?roll <some dice code>``

Role assignment
~~~~~~~~~~~~~~~

``?role <some role>``

``?unrole <some role>``

Music
~~~~~

``?play <youtube URL>``

``?pause``

``?resume``

``?stop``

``?vol <float in [0, 2]>``

Development
-----------

Local dev uses Docker.

Clone the repo, and run ``make`` to build the docker image.

Run ``make run`` to run the bot, and ``make shell`` to get a shell
inside the docker container. You may need to get some environment
variables and put them in ``.env``. If you are a Transneptunian, you can
get these from the Keybase team directory.
