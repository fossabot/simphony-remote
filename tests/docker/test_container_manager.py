from remoteappmanager.docker.container import Container
from remoteappmanager.docker.container_manager import ContainerManager
from tests import utils
from tornado.testing import AsyncTestCase, gen_test


class TestContainerManager(AsyncTestCase):
    def setUp(self):
        super().setUp()
        self.manager = ContainerManager()
        self.mock_docker_client = utils.mock_docker_client()
        self.manager.docker_client.client = self.mock_docker_client

    def test_instantiation(self):
        self.assertEqual(self.manager.containers, {})
        self.assertIsNotNone(self.manager.docker_client)

    @gen_test
    def test_start_stop(self):
        mock_client = self.mock_docker_client

        result = yield self.manager.start_container("username", "imageid")
        self.assertTrue(mock_client.start.called)
        self.assertIsInstance(result, Container)
        self.assertFalse(mock_client.stop.called)
        self.assertFalse(mock_client.remove_container.called)

        yield self.manager.stop_and_remove_container(result.docker_id)

        self.assertTrue(mock_client.stop.called)
        self.assertTrue(mock_client.remove_container.called)

    @gen_test
    def test_containers_for_image_results(self):
        ''' Test containers_for_image returns a list of Container '''
        # The mock client mocks the output of docker Client.containers
        docker_client = utils.mock_docker_client_with_running_containers()
        self.mock_docker_client = docker_client
        self.manager.docker_client.client = docker_client

        # The output should be a list of Container
        results = yield self.manager.containers_for_image("imageid")
        expected = [Container(docker_id='someid',
                              name='/remoteexec-image_3Alatest_user',
                              image_name='simphony/mayavi-4.4.4:latest',  # noqa
                              image_id='imageid', ip='0.0.0.0', port=None),
                    Container(docker_id='someid',
                              name='/remoteexec-image_3Alatest_user2',
                              image_name='simphony/mayavi-4.4.4:latest',  # noqa
                              image_id='imageid', ip='0.0.0.0', port=None)]

        for result, expected_container in zip(results, expected):
            utils.assert_containers_equal(self, result, expected_container)

    @gen_test
    def test_containers_for_image_client_api_without_user(self):
        ''' Test containers_for_images(image_id) use of Client API'''
        # The mock client mocks the output of docker Client.containers
        docker_client = utils.mock_docker_client_with_running_containers()
        self.manager.docker_client.client = docker_client

        # We assume the client.containers(filters=...) is tested by docker-py
        # Instead we test if the correct arguments are passed to the Client API
        yield self.manager.containers_for_image("imageid")
        call_args = self.manager.docker_client.client.containers.call_args

        # filters is one of the keyword argument
        self.assertIn('filters', call_args[1])
        self.assertEqual(call_args[1]['filters']['ancestor'], "imageid")

    @gen_test
    def test_containers_for_image_client_api_with_user(self):
        ''' Test containers_for_images(image_id, user) use of Client API'''
        # The mock client mocks the output of docker Client.containers
        docker_client = utils.mock_docker_client_with_running_containers()
        self.manager.docker_client.client = docker_client

        # We assume the client.containers(filters=...) is tested by docker-py
        # Instead we test if the correct arguments are passed to the Client API
        yield self.manager.containers_for_image("imageid", "userABC")
        call_args = self.manager.docker_client.client.containers.call_args

        # filters is one of the keyword argument
        self.assertIn('filters', call_args[1])
        self.assertEqual(call_args[1]['filters']['ancestor'], "imageid")
        self.assertIn("userABC", call_args[1]['filters']['label'])

    @gen_test
    def test_race_condition_spawning(self):

        # Start the operations, and retrieve the future.
        # they will stop at the first yield and not go further until
        # we yield them
        f1 = self.manager.start_container("username", "imageid")
        f2 = self.manager.start_container("username", "imageid")

        # If these yielding raise a KeyError, it is because the second
        # one tries to remove the same key from the list, but it has been
        # already removed by the first one. Race condition.
        yield f1
        yield f2

        self.assertEqual(self.mock_docker_client.start.call_count, 1)

    @gen_test
    def test_start_already_present_container(self):
        mock_client = \
            utils.mock_docker_client_with_existing_stopped_container()
        self.manager.docker_client.client = mock_client

        result = yield self.manager.start_container(
            "vagrant",
            "simphony/simphony-remote-docker:simphony-framework-paraview")
        self.assertTrue(mock_client.start.called)
        self.assertIsInstance(result, Container)

        # Stop should have been called and the container removed
        self.assertTrue(mock_client.stop.called)
        self.assertTrue(mock_client.remove_container.called)
