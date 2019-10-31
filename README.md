
Very simple simulator for first level BFRPG combat, used to test out the
effects of house rules.

Copyright 2019 Chris Gonnerman

This program simulates a battle between a canonical group of first-level
adventurers (all human, one fighter, one cleric, one thief, one magic-user) and
a group of four goblins.

It is assumed that the fight takes place in a 10' wide corridor, and that the
fighter and cleric form the front line, soaking up all attacks by the goblins
as long as they survive.  If either of them is killed, the thief moves up and
takes the place of the dead adventurer.  The magic-user is only subject to
attack if two other adventurers are killed.

Ranged attacks can be assigned to characters or monsters, with limited
ammunition.  Also, our magic-user has access to Magic Missile, which will be
cast in his or her first round.

Finally, surprise is ignored in this combat.  Initiative is rolled for each
combatant, and reach is ignored (so that identical numbers always mean
simultaneous attacks).

----------------

This is an ugly hack, folks.  If you want to change the assumptions, try out a
house rule, whatever, you edit the source code.  No options, no command line
business, nothing.  And it's probably pretty crappy code too.

When the script runs it generates a sqlite3 database containing the results of
the run.  This database, sim.db, is deleted before each run!  The database has
a single table; structurally it looks like this:

    create table simulations (
        winner      text,       # one of three values: "pcs", "monsters", "tie"
        rounds      integer,    # how many rounds were fought
        pcs         integer,    # how many PCs survived
        pchp        integer,    # how many hit points the PCs started with
        pcdam       integer,    # how many hit points of damage they took
        monsters    integer,    # how many monsters survived
        monsterhp   integer,    # how many hit points the monsters started with
        monsterdam  integer     # how many hit points of damage they took
    );

The script runs 10,000 combats by default; there's a bit of commented-out code
that you can use to run two battles back-to-back, with a fresh group of goblins
and whatever remains of the player character party.

Generally I start my analysis of the results like this:

    select count(*) from simulations where winner = 'pcs';

Now I know how many times they won out of 10,000; if the result is 8,000 (for
example), then they won 80% of the time.

Another interesting statistic is how many times all four PCs survived:

    select count(*) from simulations where winner = 'pcs' and pcs = 4;

And the average damage the party took when they won:

    select avg(pcdam) from simulations where winner = 'pcs';

NOTE CAREFULLY that you can't use double quotes " because sqlite3 treats double
quoted values as identifiers; notice that 'pcs' is the value for winner, but
pcs (no quotes) is the field name for the number of survivors.  You'll get
puzzling results if you forget this.


