import unittest
import backend


class TestBoard(unittest.TestCase):

    def setUp(self):
        self.board = backend.Board()

    def test_add_lines(self):
        lines = ((1, 2), (3, 4,), (5, 6,))
        self.board.add_lines(lines)
        self.assertItemsEqual(
            self.board.get_lines(),
            lines
        )

    def test_add_empty_lines(self):
        self.board.add_lines([])
        self.assertEqual(self.board.get_lines(), [])

    def test_get_lines_on_empty(self):
        self.assertEqual(self.board.get_lines(), [])

    def tearDown(self):
        self.board.clean()


class TestClients(unittest.TestCase):

    def test_add_client(self):
        pass

if __name__ == '__main__':
    pass
    unittest.main()
