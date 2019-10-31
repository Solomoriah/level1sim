#!/usr/bin/python

# sim.py --  Very simple simulator for first level BFRPG combat, used to test
#            out the effects of house rules.  
#
# Copyright 2019 Chris Gonnerman
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


"""
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
"""


import random, sqlite3, os


def die(n, s, b):
    return random.randint(n, s) + b


class Combatant:

    def __init__(self):
        self.hp = 0
        self.curr_hp = 0
        self.init = 0
        self.damage = (1, 6, 0)
        self.now_init = 0
        self.ac = 11
        self.spell = 0
        self.ab = 1
        self.description = "undefined"
        self.missiles = 0
        self.missileab = 0
        self.missiledamage = (1, 4, 0)

    def rollinit(self):
        self.now_init = die(1, 6, self.init)

    def attack(self, other):
        attackroll = die(1, 20, self.ab)
        if attackroll >= other.ac:
            damage = die(*self.damage)
            other.curr_hp -= damage

    def ranged(self, other):
        attackroll = die(1, 20, self.missileab)
        if attackroll >= other.ac:
            damage = die(*self.missiledamage)
            other.curr_hp -= damage
        self.missiles -= 1

    def __lt__(self, other):
        return self.now_init < other.now_init

    def __le__(self, other):
        return self.now_init <= other.now_init

    def __gt__(self, other):
        return self.now_init > other.now_init

    def __ge__(self, other):
        return self.now_init >= other.now_init

    def __eq__(self, other):
        return self.now_init == other.now_init


def reap(combatants):
    newdead = []
    i = 0

    while i < len(combatants):
        if combatants[i].curr_hp < 1:
            newdead.append(combatants.pop(i))
        else:
            i += 1

    return newdead


def runcombat(pcs, monsters):

    dead = []
    round = 0

    while pcs and monsters:
        round += 1
        for pc in pcs:
            pc.rollinit()
        for monster in monsters:
            monster.rollinit()
        for init in range(9, -3, -1):
            for i in range(len(pcs)):
                if monsters and pcs[i].now_init == init:
                    if pcs[i].spell > 0:
                        monster = monsters[die(1, len(monsters), -1)]
                        monster.curr_hp -= die(1, 6, 1)
                        pcs[i].spell -= 1
                    elif i < 2:
                        pcs[i].attack(monsters[min(i, len(monsters)-1)])
                    elif pcs[i].missiles > 0 and len(monsters) > 2:
                        pcs[i].ranged(monsters[min(i, len(monsters)-1)])
            for i in range(len(monsters)):
                if pcs and monsters[i].now_init == init:
                    if i < 2:
                        monsters[i].attack(pcs[min(i, len(pcs)-1)])
                    elif monsters[i].missiles > 0 and len(pcs) > 2:
                        monsters[i].ranged(pcs[min(i, len(pcs)-1)])
            dead += reap(pcs)
            dead += reap(monsters)

    winner = "tie"
    if pcs:
        winner = "pcs"
    if monsters:
        winner = "monsters"

    pchp = 0
    monsterhp = 0
    pcdam = 0
    monsterdam = 0

    for pc in pcs:
        pchp += pc.hp
        pcdam += pc.curr_hp - pc.hp

    for monster in monsters:
        monsterhp += monster.hp
        monsterdam += monster.curr_hp - monster.hp

    return (winner, round, len(pcs), pchp, pcdam, len(monsters), monsterhp, monsterdam)


def pcsetup():
    # allocate a fighter
    ftr = Combatant()
    ftr.description = "fighter"
    ftr.damage = (1, 8, 1)
    ftr.curr_hp = ftr.hp = die(1, 8, 0)
    ftr.curr_hp = ftr.hp = max(die(1, 8, 0), die(1, 8, 0))
#    ftr.curr_hp = ftr.hp = 8 # max hit points
    ftr.ac = 16
    ftr.ab = 2

    # allocate a cleric
    clr = Combatant()
    clr.description = "cleric"
    clr.damage = (1, 8, 0)
    clr.curr_hp = clr.hp = die(1, 6, 0)
    clr.curr_hp = clr.hp = max(die(1, 6, 0), die(1, 6, 0))
#    clr.curr_hp = clr.hp = 6 # max hit points
    clr.ac = 16

    # allocate a thief
    thf = Combatant()
    thf.description = "thief"
    thf.curr_hp = thf.hp = die(1, 4, 0)
    thf.curr_hp = thf.hp = max(die(1, 4, 0), die(1, 4, 0))
#    thf.curr_hp = thf.hp = 4 # max hit points
    thf.ac = 14
    thf.missiles = 5
    thf.missileab = 2
    thf.missiledamage = (1, 4, 0)

    # allocate a magic-user
    mag = Combatant()
    mag.description = "magic-user"
    mag.curr_hp = mag.hp = die(1, 4, 0)
    mag.curr_hp = mag.hp = max(die(1, 4, 0), die(1, 4, 0))
#    mag.curr_hp = mag.hp = 4 # max hit points
    mag.ac = 11
    mag.spell = 1
#    mag.spell = 2  # bonus spells
    mag.missiles = 5
    mag.missileab = 1
#    mag.missiles = 100 # for "arcane bolt" testing
#    mag.missileab = 2 # for "arcane bolt" testing
    mag.missiledamage = (1, 4, 0)

    return [ ftr, clr, thf, mag ]


def csvformat(seq):
    result = []
    for item in seq:
        if type(item) is type(""):
            result.append('"%s"' % item)
        else:
            result.append(str(item))
    return ",".join(result)


def monstersetup():

    monsters = []

    for i in range(4):
        gob = Combatant()
        gob.ac = 14
        gob.curr_hp = gob.hp = max(1, die(1, 8, -1))
        gob.description = "goblin"
        monsters.append(gob)

    return monsters

###############################################################################
# start of main program

try:
    os.remove("sim.db")
except:
    pass

db = sqlite3.connect("sim.db")
cursor = db.cursor()

cursor.execute("""
    create table simulations (
        winner      text,
        rounds      integer,
        pcs         integer,
        pchp        integer,
        pcdam       integer,
        monsters    integer,
        monsterhp   integer,
        monsterdam  integer
    );
""")

for i in range(10000):
    pcs = pcsetup()
    monsters = monstersetup()
    results = runcombat(pcs, monsters)
#    if pcs:
#        monsters = monstersetup()
#        results = runcombat(pcs, monsters)
    cursor.execute("""
        insert into simulations (winner, rounds, pcs, pchp, pcdam, monsters, monsterhp, monsterdam)
        values (?, ?, ?, ?, ?, ?, ?, ?)
    """, results)

db.commit()


# end of file.
