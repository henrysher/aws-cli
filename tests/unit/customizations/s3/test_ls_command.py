#!/usr/bin/env python
# Copyright 2014 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from awscli.testutils import BaseAWSCommandParamsTest
from dateutil import parser, tz


class TestLSCommand(BaseAWSCommandParamsTest):

    def test_operations_used_in_recursive_list(self):
        time_utc = "2014-01-09T20:45:49.000Z"
        self.parsed_responses = [{"CommonPrefixes": [], "Contents": [
            {"Key": "foo/bar.txt", "Size": 100,
             "LastModified": time_utc}]}]
        stdout, _, _ = self.run_cmd('s3 ls s3://bucket/ --recursive', expected_rc=0)
        call_args = self.operations_called[0][1]
        # We should not be calling the args with any delimiter because we
        # want a recursive listing.
        self.assertEqual(call_args['prefix'], '')
        self.assertEqual(call_args['bucket'], 'bucket')
        self.assertNotIn('delimiter', call_args)
        # Time is stored in UTC timezone, but the actual time displayed
        # is specific to your tzinfo, so shift the timezone to your local's.
        time_local = parser.parse(time_utc).astimezone(tz.tzlocal())
        self.assertEqual(
            stdout, '%s        100 foo/bar.txt\n'%time_local.strftime('%Y-%m-%d %H:%M:%S'))

    def test_errors_out_with_extra_arguments(self):
        stderr = self.run_cmd('s3 ls --extra-argument-foo', expected_rc=255)[1]
        self.assertIn('Unknown options', stderr)
        self.assertIn('--extra-argument-foo', stderr)

    def test_operations_use_page_size(self):
        time_utc = "2014-01-09T20:45:49.000Z"
        self.parsed_responses = [{"CommonPrefixes": [], "Contents": [
            {"Key": "foo/bar.txt", "Size": 100,
             "LastModified": time_utc}]}]
        stdout, _, _ = self.run_cmd('s3 ls s3://bucket/ --page-size 8', expected_rc=0)
        call_args = self.operations_called[0][1]
        # We should not be calling the args with any delimiter because we
        # want a recursive listing.
        self.assertEqual(call_args['prefix'], '')
        self.assertEqual(call_args['bucket'], 'bucket')
        # The page size gets translated to ``MaxKeys`` in the s3 model
        self.assertEqual(call_args['MaxKeys'], 8)

    def test_operations_use_page_size_recursive(self):
        time_utc = "2014-01-09T20:45:49.000Z"
        self.parsed_responses = [{"CommonPrefixes": [], "Contents": [
            {"Key": "foo/bar.txt", "Size": 100,
             "LastModified": time_utc}]}]
        stdout, _, _ = self.run_cmd('s3 ls s3://bucket/ --page-size 8 --recursive', expected_rc=0)
        call_args = self.operations_called[0][1]
        # We should not be calling the args with any delimiter because we
        # want a recursive listing.
        self.assertEqual(call_args['prefix'], '')
        self.assertEqual(call_args['bucket'], 'bucket')
        # The page size gets translated to ``MaxKeys`` in the s3 model
        self.assertEqual(call_args['MaxKeys'], 8)
        self.assertNotIn('delimiter', call_args)

    def test_success_rc_has_prefixes_and_objects(self):
        time_utc = "2014-01-09T20:45:49.000Z"
        self.parsed_responses = [
            {"CommonPrefixes": [{"Prefix": "foo/"}],
             "Contents": [{"Key": "foo/bar.txt", "Size": 100,
                           "LastModified": time_utc}]}
        ]
        self.run_cmd('s3 ls s3://bucket/foo', expected_rc=0)

    def test_success_rc_has_only_prefixes(self):
        self.parsed_responses = [
            {"CommonPrefixes": [{"Prefix": "foo/"}]}
        ]
        self.run_cmd('s3 ls s3://bucket/foo', expected_rc=0)

    def test_success_rc_has_only_objects(self):
        time_utc = "2014-01-09T20:45:49.000Z"
        self.parsed_responses = [
            {"Contents": [{"Key": "foo/bar.txt", "Size": 100,
             "LastModified": time_utc}]}
        ]
        self.run_cmd('s3 ls s3://bucket/foo', expected_rc=0)

    def test_success_rc_with_pagination(self):
        time_utc = "2014-01-09T20:45:49.000Z"
        # Pagination should not affect a successful return code of zero, even
        # if there are no results on the second page because there were
        # results in previous pages.
        self.parsed_responses = [
            {"CommonPrefixes": [{"Prefix": "foo/"}],
             "Contents": [{"Key": "foo/bar.txt", "Size": 100,
                           "LastModified": time_utc}]},
            {}
        ]
        self.run_cmd('s3 ls s3://bucket/foo', expected_rc=0)

    def test_success_rc_empty_bucket_no_key_given(self):
        # If no key has been provdided and the bucket is empty, it should
        # still return an rc of 0 since the user is not looking for an actual
        # object.
        self.parsed_responses = [{}]
        self.run_cmd('s3 ls s3://bucket', expected_rc=0)

    def test_fail_rc_no_objects_nor_prefixes(self):
        self.parsed_responses = [{}]
        self.run_cmd('s3 ls s3://bucket/foo', expected_rc=1)


if __name__ == "__main__":
    unittest.main()
