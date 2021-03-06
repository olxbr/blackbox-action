import datetime
import unittest
import boto3
import json
from git import GitCommandError

from unittest.mock import patch
from unittest import mock
from freezegun import freeze_time
from moto import mock_s3, mock_sts

import get_data_from_repo

import utils as test_utils

json_obj = {
    "metadata": {
        "created_at": "2022-05-27",
        "first_commit_date": "2022-06-01",
        "last_commit_date": "2022-06-27",
        "age": 1.83,
        "commit_rate": 2,
    },
    "packages": [
        ["@ant-design/colors", "5.0.1", "library", None],
        ["@ant-design/icons", "4.4.0", "library", None]
    ],
    "languages": {
        "Python": 3000
    }
}


class GetData(unittest.TestCase):
    @patch(
        "gh_api_requester.GHAPIRequests.get", side_effect=test_utils.mocked_requests_get
    )
    @patch("time.sleep", return_value=None)
    def test_get_repo_languages(self, mock_get, mock_time):
        repos = get_data_from_repo.get_repo_languages(repo="tech-radar")
        self.assertEqual(repos, {"kotlin": "5000", "python": "4000"})

    @patch(
        "gh_api_requester.GHAPIRequests.get", side_effect=test_utils.mocked_requests_get
    )
    @patch("time.sleep", return_value=None)
    def test_get_repo_return_0_languages(self, mock_get, mock_time):
        repos = get_data_from_repo.get_repo_languages(repo="zero-lang-repo")

        self.assertEqual(repos, {})

    @patch(
        "gh_api_requester.GHAPIRequests.get", side_effect=test_utils.mocked_requests_get
    )
    @patch("time.sleep", return_value=None)
    def test_get_repo_creation_date(self, mock_get, mock_time):
        creation_date = get_data_from_repo.get_creation_date(repo="tech-radar")

        self.assertEqual(creation_date, "2022-04-08T17:46:53Z")

    @patch("get_data_from_repo.repo")
    @freeze_time("2022-05-04")
    def test_get_repo_age_metadata_commit_based(self, mock_repo):
        mock_iterable = mock.Mock()
        mock_repo.iter_commits.return_value = [mock_iterable]
        mock_iterable.committed_datetime = datetime.datetime.strptime(
            "2022-04-04 +0000", "%Y-%m-%d %z"
        )

        age, _, _ = get_data_from_repo.get_repo_age_metadata_commit_based()

        self.assertEqual(age, 1.0)

    @patch("get_data_from_repo.repo")
    @freeze_time("2022-05-04")
    def test_get_repo_first_commit_date(self, mock_repo):
        mock_iterable = mock.Mock()
        mock_repo.iter_commits.return_value = [mock_iterable]
        mock_iterable.committed_datetime = datetime.datetime.strptime(
            "2022-04-04 +0000", "%Y-%m-%d %z"
        )

        (
            _,
            first_commit_date,
            _,
        ) = get_data_from_repo.get_repo_age_metadata_commit_based()

        self.assertEqual(first_commit_date, "2022-04-04 +0000")

    @patch("get_data_from_repo.repo")
    @freeze_time("2022-05-04")
    def test_get_repo_last_commit_date(self, mock_repo):
        mock_iterable_last = mock.Mock()
        mock_iterable_first = mock.Mock()
        mock_repo.iter_commits.return_value = [mock_iterable_last, mock_iterable_first]
        mock_iterable_last.committed_datetime = datetime.datetime.strptime(
            "2022-04-04 +0000", "%Y-%m-%d %z"
        )
        mock_iterable_first.committed_datetime = datetime.datetime.strptime(
            "2021-04-04 +0000", "%Y-%m-%d %z"
        )

        (
            _,
            _,
            last_commit_date,
        ) = get_data_from_repo.get_repo_age_metadata_commit_based()

        self.assertEqual(last_commit_date, "2022-04-04 +0000")

    @patch("get_data_from_repo.repo")
    @freeze_time("2022-05-04")
    def test_get_repo_age_commit_basd_clean_tree(self, mock_repo):
        mock_repo.iter_commits.side_effect = GitCommandError(
            "git rev-list master --", 128
        )

        age, _, _ = get_data_from_repo.get_repo_age_metadata_commit_based()

        self.assertEqual(age, 0.0)

    @patch("get_data_from_repo.repo")
    @freeze_time("2022-05-04")
    def test_get_repo_first_commit_date_basd_clean_tree(self, mock_repo):
        mock_repo.iter_commits.side_effect = GitCommandError(
            "git rev-list master --", 128
        )

        (
            _,
            first_commit_date,
            _,
        ) = get_data_from_repo.get_repo_age_metadata_commit_based()

        self.assertEqual(first_commit_date, None)

    @patch("get_data_from_repo.repo")
    @freeze_time("2022-05-04")
    def test_get_repo_commit_rate(self, mock_repo):
        mock_iterable_list = []
        for i in range(1, 10):
            mock_iterable = mock.Mock()
            mock_iterable.committed_datetime = datetime.datetime.strptime(
                f"2022-04-0{i} +0000", "%Y-%m-%d %z"
            )
            mock_iterable_list.append(mock_iterable)
        mock_repo.iter_commits.return_value = mock_iterable_list

        cr = get_data_from_repo.get_repo_commit_rate()

        self.assertEqual(cr, 0.3)

    @patch("get_data_from_repo.repo")
    @freeze_time("2022-05-04")
    def test_get_repo_cr_commit_basd_with_clean_tree(self, mock_repo):
        mock_repo.iter_commits.side_effect = GitCommandError(
            "git rev-list master --", 128
        )

        cr = get_data_from_repo.get_repo_commit_rate()

        self.assertEqual(cr, 0.0)

    @patch(
        "gh_api_requester.GHAPIRequests.get", side_effect=test_utils.mocked_requests_get
    )
    @patch("get_data_from_repo.repo")
    @freeze_time("2022-05-04")
    def test_get_repo_metadata_with_clean_tree(self, mock_repo, mock_get):
        mock_repo.iter_commits.side_effect = GitCommandError(
            "git rev-list main --", 128
        )


        (
            age,
            cr,
            created_at,
            first_commit_date,
            last_commit_date,
            commits,
        )= get_data_from_repo.get_repo_metadata(
            "tech-radar", "main"
        )

        self.assertEqual(cr, 0.0)
        self.assertEqual(age, 0.0)
        self.assertEqual(created_at, "2022-04-08T17:46:53Z")
        self.assertEqual(commits, [{}])

    @patch(
        "gh_api_requester.GHAPIRequests.get", side_effect=test_utils.mocked_requests_get
    )
    @patch("get_data_from_repo.repo")
    @freeze_time("2022-05-01")
    def test_get_repo_metadata(self, mock_repo, mock_get):
        mock_iterable_list = []
        for i in range(9, 0, -1):
            mock_iterable = mock.Mock()
            mock_iterable.committed_datetime = datetime.datetime.strptime(
                f"2022-04-0{i} +0000", "%Y-%m-%d %z"
            )
            mock_iterable_list.append(mock_iterable)
        mock_repo.iter_commits.return_value = mock_iterable_list

        (
            age,
            cr,
            created_at,
            first_commit_date,
            last_commit_date,
            commits,
        )= get_data_from_repo.get_repo_metadata(
            "tech-radar", "main"
        )

        self.assertEqual(cr, 0.3)
        self.assertEqual(age, 1.0)
        self.assertEqual(created_at, "2022-04-08T17:46:53Z")
        self.assertEqual(len(commits), 9)

    @mock_s3
    @mock_sts
    def test_load_to_s3_with_assume_role_throws_exception_if_bucket_doesnt_exist(self):
        repo = "tech-radar"
        bucket = "blackbox"
        role = "arn:aws:iam::000000000000:role/blackbox"
        ext_id = "00000000-0000-0000-0000-000000000000"

        with self.assertRaises(Exception) as context:
            get_data_from_repo.load_to_s3(repo, json_obj, bucket, role, ext_id)

        self.assertTrue("NoSuchBucket" in str(context.exception))

    @mock_s3
    @mock_sts
    def test_load_to_s3_with_assume_role_throws_exception_if_role_is_invalid(self):
        repo = "tech-radar"
        bucket = "blackbox"
        role = ""
        ext_id = ""

        conn = boto3.resource("s3", region_name="us-east-1")
        conn.create_bucket(Bucket="blackbox")

        with self.assertRaises(Exception) as context:
            get_data_from_repo.load_to_s3(repo, json_obj, bucket, role, ext_id)

        self.assertTrue("Parameter validation failed" in str(context.exception))

    @mock_s3
    @mock_sts
    def test_load_to_s3_pushes_to_s3(self):
        repo = "tech-radar"
        bucket = "blackbox"
        role = "arn:aws:iam::000000000000:role/blackbox"
        ext_id = "00000000-0000-0000-0000-000000000000"

        conn = boto3.resource("s3", region_name="us-east-1")
        conn.create_bucket(Bucket=bucket)
        s3_bucket = conn.Bucket(bucket)

        get_data_from_repo.load_to_s3(repo, json_obj, bucket, role, ext_id)

        for obj in s3_bucket.objects.all():
            key = obj.key
            self.assertRegex(key, r'\/(dt=)?\d{4}-\d{2}-\d{2}(-|\/)?[-\w]+-\d+.(parquet|json)$')  # fmt: skip

    def test_compressor(self):
        expected_output = {
            "repo": "tech-radar",
            "metadata": {
                "age": 10.1,
                "commit_rate": 3.0,
                "created_at": "2022-04-08T17:46:53Z",
                "first_commit_date": "2022-04-08T17:46:53Z",
                "last_commit_date": "2022-05-26T14:06:54Z",
                "commits": [
                            {
                                'sha': 'checo11c005c284000bb83b0f120df9f452fe320',
                                'commied_at': '2022-05-29 +0200',
                                'author': 'Sergio Perez',
                                'message': 'Monaco win',
                            }
                ],
            },
            "languages": {"python": 1000},
            "packages": [
                {
                    "name": "not_a_pkg",
                    "type": "not_pkg",
                    "version": None,
                    "bom_ref": None,
                }
            ],
        }

        syft_output = [
            {
                "type": "not_pkg",
                "name": "not_a_pkg",
                "version": None,
                "bom_ref": None,
            }
        ]
        sbom_data = get_data_from_repo.compressor(
            repo="tech-radar",
            age=10.1,
            commit_rate=3.0,
            languages={"python": 1000},
            packages=syft_output,
            created_at="2022-04-08T17:46:53Z",
            first_commit_date="2022-04-08T17:46:53Z",
            last_commit_date="2022-05-26T14:06:54Z",
            commits=[
                        {
                            'sha': 'checo11c005c284000bb83b0f120df9f452fe320',
                            'commied_at': '2022-05-29 +0200',
                            'author': 'Sergio Perez',
                            'message': 'Monaco win',
                        }
            ],
        )

        self.assertDictEqual(sbom_data, expected_output)

    def test_compressor_without_bom_ref(self):
        expected_output = {
            "repo": "tech-radar",
            "metadata": {
                "age": 10.1,
                "commit_rate": 3.0,
                "created_at": "2022-04-08T17:46:53Z",
                "first_commit_date": "2022-04-08T17:46:53Z",
                "last_commit_date": "2022-05-26T14:06:54Z",
                "commits": [{}]
            },
            "languages": {"python": 1000},
            "packages": [
                {
                    "name": "not_a_pkg",
                    "type": "not_pkg",
                    "version": None,
                    "bom_ref": None,
                }
            ],
        }

        syft_output = [
            {
                "type": "not_pkg",
                "name": "not_a_pkg",
                "version": 0.0,
            }
        ]
        sbom_data = get_data_from_repo.compressor(
            repo="tech-radar",
            age=10.1,
            commit_rate=3.0,
            languages={"python": 1000},
            packages=syft_output,
            last_commit_date="2022-05-26T14:06:54Z",
            first_commit_date="2022-04-08T17:46:53Z",
            created_at="2022-04-08T17:46:53Z",
            commits=[{}]
        )

        self.assertDictEqual(sbom_data, expected_output)

    def test_compressor_without_version(self):
        expected_output = {
            "repo": "tech-radar",
            "metadata": {
                "age": 10.1,
                "commit_rate": 3.0,
                "created_at": "2022-04-08T17:46:53Z",
                "first_commit_date": "2022-04-08T17:46:53Z",
                "last_commit_date": "2022-05-26T14:06:54Z",
                "commits": [
                            {
                                'sha': 'checo11c005c284000bb83b0f120df9f452fe320',
                                'commied_at': '2022-05-29 +0200',
                                'author': 'Sergio Perez',
                                'message': 'Monaco win',
                            }
                ]
            },
            "languages": {"python": 1000},
            "packages": [
                {
                    "name": "not_a_pkg",
                    "type": "not_pkg",
                    "version": None,
                    "bom_ref": None,
                }
            ],
        }

        syft_output = [
            {
                "type": "not_pkg",
                "name": "not_a_pkg",
                "bom_ref": 0.0,
            }
        ]
        sbom_data = get_data_from_repo.compressor(
            repo="tech-radar",
            age=10.1,
            commit_rate=3.0,
            languages={"python": 1000},
            packages=syft_output,
            created_at="2022-04-08T17:46:53Z",
            first_commit_date="2022-04-08T17:46:53Z",
            last_commit_date="2022-05-26T14:06:54Z",
            commits=[
                        {
                            'sha': 'checo11c005c284000bb83b0f120df9f452fe320',
                            'commied_at': '2022-05-29 +0200',
                            'author': 'Sergio Perez',
                            'message': 'Monaco win',
                        }
            ],
        )

        self.assertDictEqual(sbom_data, expected_output)

    def test_get_files_by_regex_recursive_no_parameters_passed(self):
        lis_of_files_as_should_be = [
            "dev.yml",
            "Makefile",
            "src/code.py",
            "src/tests.py",
            "src/config/config.yml",
        ]
        with patch("os.listdir") as mocked_listdir:
            with patch("os.path.isdir") as mocked_isdir:
                # fmt: off
                mocked_listdir.side_effect = [
                    ["dev.yml", "Makefile", "src"],
                    ["code.py", "tests.py", "config"],
                    ["config.yml"],
                ]
                mocked_isdir.side_effect = [
                    False, False, True,
                    False, False, True,
                    False,
                ]
                # fmt: on

                list_of_files = get_data_from_repo.get_files_by_regex()

        self.assertEqual(lis_of_files_as_should_be, list_of_files)

    def test_get_files_by_regex_recursive(self):
        lis_of_files_as_should_be = [
            "Dockerfile",
            "src/config/Dockerfile.test",
        ]
        with patch("os.listdir") as mocked_listdir:
            with patch("os.path.isdir") as mocked_isdir:
                # fmt: off
                mocked_listdir.side_effect = [
                    ["dev.yml", "Dockerfile", "src"],
                    ["code.py", "tests.py", "config"],
                    ["config.yml", "Dockerfile.test"],
                ]
                mocked_isdir.side_effect = [
                    False, False, True,
                    False, False, True,
                    False, False,
                ]
                # fmt: on

                list_of_files = get_data_from_repo.get_files_by_regex(
                    ".*Dockerfile*"
                )

        self.assertEqual(lis_of_files_as_should_be, list_of_files)
