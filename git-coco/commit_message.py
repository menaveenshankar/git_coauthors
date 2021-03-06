from abc import abstractmethod
from time import sleep
from utils import read_authors_file
from os.path import exists
import sys


class CommitMessage(object):
    def __init__(self, msg):
        self._message = msg

    @property
    @abstractmethod
    def message(self):
        return self._message

    @message.setter
    def message(self, msg):
        self._message = msg


class CoauthorsCommitMessage(CommitMessage):
    def __init__(self, coauthors, authors_dict, config_coauthors):
        super(CoauthorsCommitMessage, self).__init__("")
        self._coauthors = self.non_empty_coauthors_list(coauthors)
        self._config = config_coauthors
        self.authors_dict = authors_dict

    def non_empty_coauthors_list(self, coauthors):
        valid_coauths = [x.strip().upper() for x in coauthors.split(',')]
        return list(filter(lambda x: x, valid_coauths))

    def _prune_incorrect_coauthor_initials(self):
        authorlst = set(self.authors_dict.keys())
        commit_authors = set(self._coauthors)
        correct_coauthors = authorlst.intersection(commit_authors)
        incorrect_coauthors = commit_authors.difference(authorlst)
        if incorrect_coauthors:
            print("[INFO]: These initials are incorrect {}. \n Please check and add them manually\n".format(
                list(incorrect_coauthors)))
            sleep(2)
        return correct_coauthors

    def _get_coauthor_name_email(self):
        self._coauthors = self._prune_incorrect_coauthor_initials()
        return [self.authors_dict[x.strip().upper()].split(',') for x in self._coauthors]

    @property
    def message(self):
        if not self._coauthors:
            self._message = '\n'
        else:
            prefix_str = 'Co-authored-by: {}'
            _coauth_fmt = lambda x: '{} <{}@{}>'.format(x[0].strip(), x[1].strip(), self._config['domain'])

            coauths_lst = self._get_coauthor_name_email()
            coauths_str = [prefix_str.format(_coauth_fmt(x)) for x in coauths_lst]
            # git expects co-authors after two blank lines
            self._message = '\n\n' + '\n'.join(coauths_str) + '\n\n'
        return self._message


class ReadCoauthorMessageWrapper(CommitMessage):
    def __init__(self, config):
        super(ReadCoauthorMessageWrapper, self).__init__("")
        self._config_coauthors = config
        self.read_authors_msg()

    def input_coauthor_initials(self):
        sys.stdin = open('/dev/tty', 'r')
        coauthors = input(
            """\n[INFO]: ADD co-authors (if any) as a comma separated list of 2 letter initials.
            example input - ts, ck (for Tony Stark and Clark Kent )
            Open $GIT_COCO/authors.txt to view the current list of authors for this project.
            \n[INPUT]: Enter co-author(s) initials: """)
        return coauthors

    def _read_authors_msg_eidetic(self, authors_file):
        coauths_csv = self.input_coauthor_initials()
        authors_dict = read_authors_file(authors_file)
        self._message = CoauthorsCommitMessage(coauths_csv, authors_dict, self._config_coauthors).message

    def _read_authors_msg_autosuggest(self, git_coco_msg_file):
        with open(git_coco_msg_file) as f:
            coauths_msg = f.read()
        self._message = coauths_msg

    def read_authors_msg(self):
        git_coco_msg_file = self._config_coauthors['coauthors_git_msg_file']
        if exists(git_coco_msg_file):
            self._read_authors_msg_autosuggest(git_coco_msg_file)
        else:
            self._read_authors_msg_eidetic(self._config_coauthors['authors_file'])

    @property
    def message(self):
        return self._message


class IssueNumberCommitMessage(CommitMessage):
    def __init__(self, repo, config):
        super(IssueNumberCommitMessage, self).__init__("")
        self.repo = repo
        self._config_issue = config
        self._issue_number = self.parse_issue_number_from_branch() if self._config_issue['use_issue_in_msg'] else ""

    def parse_issue_number_from_branch(self):
        if self.repo.head.is_detached:  return ''
        issue_number = IssueNumberCommitMessage.is_issue_number_in_branch(self.repo.active_branch.name)
        # if issue number is part of the branch name
        if issue_number is None:
            sys.stdin = open('/dev/tty', 'r')
            issue_number = str(input('[INPUT]: Enter issue number (optional): '))

        return issue_number

    @staticmethod
    def is_issue_number_in_branch(active_branch):
        # check if branch ends with "_issuexxxxx" where xxxxx is the issue number
        issue_number = active_branch.lower().split('_')[-1]
        return issue_number[5:] if 'issue' in issue_number else None

    @property
    def message(self):
        if self._issue_number:
            issue_url = self._config_issue['issue_url_base'] + self._issue_number
            self._message = '\nItem: {}\n{}\n\n'.format(self._issue_number, issue_url)

        return self._message
