from abc import ABC, abstractmethod
from time import sleep
import sys


class CommitMessage(ABC):
    def __init__(self):
        self._message = ""

    @property
    @abstractmethod
    def message(self):
        return self._message


class CoauthorsCommitMessage(CommitMessage):
    def __init__(self, coauthors, authors_dict, config_coauthors):
        super(CoauthorsCommitMessage, self).__init__()
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
            return '\n'
        else:
            prefix_str = 'Co-authored-by: {}'
            _coauth_fmt = lambda x: '{} <{}@{}>'.format(x[0].strip(), x[1].strip(), self._config['domain'])

            coauths_lst = self._get_coauthor_name_email()
            coauths_str = [prefix_str.format(_coauth_fmt(x)) for x in coauths_lst]
            # git expects co-authors after two blank lines
            return '\n\n' + '\n'.join(coauths_str) + '\n\n'


class IssueNumberCommitMessage(CommitMessage):
    def __init__(self, repo, config):
        super(IssueNumberCommitMessage, self).__init__()
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
        return issue_number[2:] if 'issue' in issue_number else None

    @property
    def message(self):
        if self._issue_number:
            issue_url = self._config_issue['issue_url_base'] + self._issue_number
            self._issue_number = '\nItem: {}\n{}\n'.format(self._issue_number, issue_url)

        return self._issue_number