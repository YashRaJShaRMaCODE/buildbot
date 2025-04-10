# This file is part of Buildbot.  Buildbot is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members


from twisted.internet import defer
from twisted.trial import unittest

from buildbot.data import steps
from buildbot.db.steps import StepModel
from buildbot.db.steps import UrlModel
from buildbot.test import fakedb
from buildbot.test.fake import fakemaster
from buildbot.test.reactor import TestReactorMixin
from buildbot.test.util import endpoint
from buildbot.test.util import interfaces
from buildbot.util import epoch2datetime

TIME1 = 2001111
TIME2 = 2002222
TIME3 = 2003333
TIME4 = 2004444


class StepEndpoint(endpoint.EndpointMixin, unittest.TestCase):
    endpointClass = steps.StepEndpoint
    resourceTypeClass = steps.Step

    @defer.inlineCallbacks
    def setUp(self):
        yield self.setUpEndpoint()
        yield self.master.db.insert_test_data([
            fakedb.Worker(id=47, name='linux'),
            fakedb.Builder(id=77, name='builder77'),
            fakedb.Master(id=88),
            fakedb.Buildset(id=8822),
            fakedb.BuildRequest(id=82, builderid=77, buildsetid=8822),
            fakedb.Build(
                id=30, builderid=77, number=7, masterid=88, buildrequestid=82, workerid=47
            ),
            fakedb.Step(
                id=70,
                number=0,
                name='one',
                buildid=30,
                started_at=TIME1,
                locks_acquired_at=TIME2,
                complete_at=TIME3,
                results=0,
            ),
            fakedb.Step(
                id=71,
                number=1,
                name='two',
                buildid=30,
                started_at=TIME2,
                locks_acquired_at=TIME3,
                complete_at=TIME4,
                results=2,
                urls_json='[{"name":"url","url":"http://url"}]',
            ),
            fakedb.Step(id=72, number=2, name='three', buildid=30, started_at=TIME4, hidden=True),
        ])

    @defer.inlineCallbacks
    def test_get_existing(self):
        step = yield self.callGet(('steps', 72))
        self.validateData(step)
        self.assertEqual(
            step,
            {
                'buildid': 30,
                'complete': False,
                'complete_at': None,
                'name': 'three',
                'number': 2,
                'results': None,
                'started_at': epoch2datetime(TIME4),
                "locks_acquired_at": None,
                'state_string': '',
                'stepid': 72,
                'urls': [],
                'hidden': True,
            },
        )

    @defer.inlineCallbacks
    def test_get_existing_buildid_name(self):
        step = yield self.callGet(('builds', 30, 'steps', 'two'))
        self.validateData(step)
        self.assertEqual(step['stepid'], 71)

    @defer.inlineCallbacks
    def test_get_existing_buildid_number(self):
        step = yield self.callGet(('builds', 30, 'steps', 1))
        self.validateData(step)
        self.assertEqual(step['stepid'], 71)

    @defer.inlineCallbacks
    def test_get_existing_builder_name(self):
        step = yield self.callGet(('builders', 77, 'builds', 7, 'steps', 'two'))
        self.validateData(step)
        self.assertEqual(step['stepid'], 71)

    @defer.inlineCallbacks
    def test_get_existing_buildername_name(self):
        step = yield self.callGet(('builders', 'builder77', 'builds', 7, 'steps', 'two'))
        self.validateData(step)
        self.assertEqual(step['stepid'], 71)

    @defer.inlineCallbacks
    def test_get_existing_builder_number(self):
        step = yield self.callGet(('builders', 77, 'builds', 7, 'steps', 1))
        self.validateData(step)
        self.assertEqual(step['stepid'], 71)

    @defer.inlineCallbacks
    def test_get_missing_buildername_builder_number(self):
        step = yield self.callGet(('builders', 'builder77_nope', 'builds', 7, 'steps', 1))
        self.assertEqual(step, None)

    @defer.inlineCallbacks
    def test_get_missing(self):
        step = yield self.callGet(('steps', 9999))
        self.assertEqual(step, None)


class StepsEndpoint(endpoint.EndpointMixin, unittest.TestCase):
    endpointClass = steps.StepsEndpoint
    resourceTypeClass = steps.Step

    @defer.inlineCallbacks
    def setUp(self):
        yield self.setUpEndpoint()
        yield self.master.db.insert_test_data([
            fakedb.Worker(id=47, name='linux'),
            fakedb.Builder(id=77, name='builder77'),
            fakedb.Master(id=88),
            fakedb.Buildset(id=8822),
            fakedb.BuildRequest(id=82, builderid=77, buildsetid=8822),
            fakedb.Build(
                id=30, builderid=77, number=7, masterid=88, buildrequestid=82, workerid=47
            ),
            fakedb.Build(
                id=31, builderid=77, number=8, masterid=88, buildrequestid=82, workerid=47
            ),
            fakedb.Step(
                id=70,
                number=0,
                name='one',
                buildid=30,
                started_at=TIME1,
                locks_acquired_at=TIME2,
                complete_at=TIME3,
                results=0,
            ),
            fakedb.Step(
                id=71,
                number=1,
                name='two',
                buildid=30,
                started_at=TIME2,
                locks_acquired_at=TIME3,
                complete_at=TIME4,
                results=2,
                urls_json='[{"name":"url","url":"http://url"}]',
            ),
            fakedb.Step(id=72, number=2, name='three', buildid=30, started_at=TIME4),
            fakedb.Step(id=73, number=0, name='otherbuild', buildid=31, started_at=TIME3),
        ])

    @defer.inlineCallbacks
    def test_get_buildid(self):
        steps = yield self.callGet(('builds', 30, 'steps'))

        for step in steps:
            self.validateData(step)

        self.assertEqual([s['number'] for s in steps], [0, 1, 2])

    @defer.inlineCallbacks
    def test_get_builder(self):
        steps = yield self.callGet(('builders', 77, 'builds', 7, 'steps'))

        for step in steps:
            self.validateData(step)

        self.assertEqual([s['number'] for s in steps], [0, 1, 2])

    @defer.inlineCallbacks
    def test_get_buildername(self):
        steps = yield self.callGet(('builders', 'builder77', 'builds', 7, 'steps'))

        for step in steps:
            self.validateData(step)

        self.assertEqual([s['number'] for s in steps], [0, 1, 2])


class Step(TestReactorMixin, interfaces.InterfaceTests, unittest.TestCase):
    @defer.inlineCallbacks
    def setUp(self):
        self.setup_test_reactor()
        self.master = yield fakemaster.make_master(self, wantMq=True, wantDb=True, wantData=True)
        self.rtype = steps.Step(self.master)

        yield self.master.db.insert_test_data([
            fakedb.Worker(id=47, name='linux'),
            fakedb.Builder(id=77, name='builder77'),
            fakedb.Master(id=88),
            fakedb.Buildset(id=8822),
            fakedb.BuildRequest(id=82, builderid=77, buildsetid=8822),
            fakedb.Build(
                id=10, builderid=77, number=7, masterid=88, buildrequestid=82, workerid=47
            ),
        ])

    def test_signature_addStep(self):
        @self.assertArgSpecMatches(
            self.master.data.updates.addStep,  # fake
            self.rtype.addStep,
        )  # real
        def addStep(self, buildid, name):
            pass

    @defer.inlineCallbacks
    def test_addStep(self):
        stepid, number, name = yield self.rtype.addStep(buildid=10, name='name')
        msgBody = {
            'buildid': 10,
            'complete': False,
            'complete_at': None,
            'name': name,
            'number': number,
            'results': None,
            'started_at': None,
            "locks_acquired_at": None,
            'state_string': 'pending',
            'stepid': stepid,
            'urls': [],
            'hidden': False,
        }
        self.master.mq.assertProductions([
            (('builds', '10', 'steps', str(stepid), 'new'), msgBody),
            (('steps', str(stepid), 'new'), msgBody),
        ])
        step = yield self.master.db.steps.getStep(stepid)
        self.assertEqual(
            step,
            StepModel(
                buildid=10,
                complete_at=None,
                id=stepid,
                name=name,
                number=number,
                results=None,
                started_at=None,
                locks_acquired_at=None,
                state_string='pending',
                urls=[],
                hidden=False,
            ),
        )

    @defer.inlineCallbacks
    def test_fake_addStep(self):
        self.assertEqual(len((yield self.master.data.updates.addStep(buildid=10, name='ten'))), 3)

    def test_signature_startStep(self):
        @self.assertArgSpecMatches(self.master.data.updates.startStep, self.rtype.startStep)
        def addStep(self, stepid, started_at=None, locks_acquired=False):
            pass

    @defer.inlineCallbacks
    def test_startStep(self):
        self.reactor.advance(TIME1)
        stepid, _, _ = yield self.master.db.steps.addStep(
            buildid=10, name='ten', state_string='pending'
        )
        yield self.rtype.startStep(stepid=stepid)

        msgBody = {
            'buildid': 10,
            'complete': False,
            'complete_at': None,
            'name': 'ten',
            'number': 0,
            'results': None,
            'started_at': epoch2datetime(TIME1),
            "locks_acquired_at": None,
            'state_string': 'pending',
            'stepid': stepid,
            'urls': [],
            'hidden': False,
        }
        self.master.mq.assertProductions([
            (('builds', '10', 'steps', str(stepid), 'started'), msgBody),
            (('steps', str(stepid), 'started'), msgBody),
        ])
        step = yield self.master.db.steps.getStep(stepid)
        self.assertEqual(
            step,
            StepModel(
                buildid=10,
                complete_at=None,
                id=stepid,
                name='ten',
                number=0,
                results=None,
                started_at=epoch2datetime(TIME1),
                locks_acquired_at=None,
                state_string='pending',
                urls=[],
                hidden=False,
            ),
        )

    @defer.inlineCallbacks
    def test_startStep_no_locks(self):
        self.reactor.advance(TIME1)
        stepid, _, _ = yield self.master.db.steps.addStep(
            buildid=10, name="ten", state_string="pending"
        )
        yield self.rtype.startStep(stepid=stepid, locks_acquired=True)

        msgBody = {
            "buildid": 10,
            "complete": False,
            "complete_at": None,
            "name": "ten",
            "number": 0,
            "results": None,
            "started_at": epoch2datetime(TIME1),
            "locks_acquired_at": epoch2datetime(TIME1),
            "state_string": "pending",
            "stepid": stepid,
            "urls": [],
            "hidden": False,
        }
        self.master.mq.assertProductions([
            (("builds", "10", "steps", str(stepid), "started"), msgBody),
            (("steps", str(stepid), "started"), msgBody),
        ])
        step = yield self.master.db.steps.getStep(stepid)
        self.assertEqual(
            step,
            StepModel(
                buildid=10,
                complete_at=None,
                id=stepid,
                name="ten",
                number=0,
                results=None,
                started_at=epoch2datetime(TIME1),
                locks_acquired_at=epoch2datetime(TIME1),
                state_string="pending",
                urls=[],
                hidden=False,
            ),
        )

    @defer.inlineCallbacks
    def test_startStep_acquire_locks(self):
        self.reactor.advance(TIME1)
        stepid, _, _ = yield self.master.db.steps.addStep(
            buildid=10, name='ten', state_string='pending'
        )
        yield self.rtype.startStep(stepid=stepid)
        self.reactor.advance(TIME2 - TIME1)
        self.master.mq.clearProductions()
        yield self.rtype.set_step_locks_acquired_at(stepid=stepid)

        msgBody = {
            'buildid': 10,
            'complete': False,
            'complete_at': None,
            'name': 'ten',
            'number': 0,
            'results': None,
            'started_at': epoch2datetime(TIME1),
            "locks_acquired_at": epoch2datetime(TIME2),
            'state_string': 'pending',
            'stepid': stepid,
            'urls': [],
            'hidden': False,
        }
        self.master.mq.assertProductions([
            (('builds', '10', 'steps', str(stepid), 'updated'), msgBody),
            (('steps', str(stepid), 'updated'), msgBody),
        ])
        step = yield self.master.db.steps.getStep(stepid)
        self.assertEqual(
            step,
            StepModel(
                buildid=10,
                complete_at=None,
                id=stepid,
                name='ten',
                number=0,
                results=None,
                started_at=epoch2datetime(TIME1),
                locks_acquired_at=epoch2datetime(TIME2),
                state_string='pending',
                urls=[],
                hidden=False,
            ),
        )

    def test_signature_setStepStateString(self):
        @self.assertArgSpecMatches(
            self.master.data.updates.setStepStateString,  # fake
            self.rtype.setStepStateString,
        )  # real
        def setStepStateString(self, stepid, state_string):
            pass

    @defer.inlineCallbacks
    def test_setStepStateString(self):
        stepid, _, _ = yield self.master.db.steps.addStep(
            buildid=10, name='ten', state_string='pending'
        )
        yield self.rtype.setStepStateString(stepid=stepid, state_string='hi')

        msgBody = {
            'buildid': 10,
            'complete': False,
            'complete_at': None,
            'name': 'ten',
            'number': 0,
            'results': None,
            'started_at': None,
            "locks_acquired_at": None,
            'state_string': 'hi',
            'stepid': stepid,
            'urls': [],
            'hidden': False,
        }
        self.master.mq.assertProductions([
            (('builds', '10', 'steps', str(stepid), 'updated'), msgBody),
            (('steps', str(stepid), 'updated'), msgBody),
        ])
        step = yield self.master.db.steps.getStep(stepid)
        self.assertEqual(
            step,
            StepModel(
                buildid=10,
                complete_at=None,
                id=stepid,
                name='ten',
                number=0,
                results=None,
                started_at=None,
                locks_acquired_at=None,
                state_string='hi',
                urls=[],
                hidden=False,
            ),
        )

    def test_signature_finishStep(self):
        @self.assertArgSpecMatches(
            self.master.data.updates.finishStep,  # fake
            self.rtype.finishStep,
        )  # real
        def finishStep(self, stepid, results, hidden):
            pass

    @defer.inlineCallbacks
    def test_finishStep(self):
        stepid, _, _ = yield self.master.db.steps.addStep(
            buildid=10, name='ten', state_string='pending'
        )
        self.reactor.advance(TIME1)
        yield self.rtype.startStep(stepid=stepid)
        yield self.rtype.set_step_locks_acquired_at(stepid=stepid)
        self.reactor.advance(TIME2 - TIME1)
        self.master.mq.clearProductions()
        yield self.rtype.finishStep(stepid=stepid, results=9, hidden=False)

        msgBody = {
            'buildid': 10,
            'complete': True,
            'complete_at': epoch2datetime(TIME2),
            'name': 'ten',
            'number': 0,
            'results': 9,
            'started_at': epoch2datetime(TIME1),
            "locks_acquired_at": epoch2datetime(TIME1),
            'state_string': 'pending',
            'stepid': stepid,
            'urls': [],
            'hidden': False,
        }
        self.master.mq.assertProductions([
            (('builds', '10', 'steps', str(stepid), 'finished'), msgBody),
            (('steps', str(stepid), 'finished'), msgBody),
        ])
        step = yield self.master.db.steps.getStep(stepid)
        self.assertEqual(
            step,
            StepModel(
                buildid=10,
                complete_at=epoch2datetime(TIME2),
                id=stepid,
                name='ten',
                number=0,
                results=9,
                started_at=epoch2datetime(TIME1),
                locks_acquired_at=epoch2datetime(TIME1),
                state_string='pending',
                urls=[],
                hidden=False,
            ),
        )

    def test_signature_addStepURL(self):
        @self.assertArgSpecMatches(
            self.master.data.updates.addStepURL,  # fake
            self.rtype.addStepURL,
        )  # real
        def addStepURL(self, stepid, name, url):
            pass

    @defer.inlineCallbacks
    def test_addStepURL(self):
        stepid, _, _ = yield self.master.db.steps.addStep(
            buildid=10, name='ten', state_string='pending'
        )
        yield self.rtype.addStepURL(stepid=stepid, name="foo", url="bar")

        msgBody = {
            'buildid': 10,
            'complete': False,
            'complete_at': None,
            'name': 'ten',
            'number': 0,
            'results': None,
            'started_at': None,
            "locks_acquired_at": None,
            'state_string': 'pending',
            'stepid': stepid,
            'urls': [{'name': 'foo', 'url': 'bar'}],
            'hidden': False,
        }
        self.master.mq.assertProductions([
            (('builds', '10', 'steps', str(stepid), 'updated'), msgBody),
            (('steps', str(stepid), 'updated'), msgBody),
        ])
        step = yield self.master.db.steps.getStep(stepid)
        self.assertEqual(
            step,
            StepModel(
                buildid=10,
                complete_at=None,
                id=stepid,
                name='ten',
                number=0,
                results=None,
                started_at=None,
                locks_acquired_at=None,
                state_string='pending',
                urls=[UrlModel(name='foo', url='bar')],
                hidden=False,
            ),
        )
