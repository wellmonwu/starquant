#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..common.datastruct import AccountEvent

class AccountManager(object):
    def __init__(self, config_server):
        self._config_server = config_server
        self._account_dict = {}            # account id ==> account
        self.reset()

    def reset(self):
        self._account_dict.clear()
        # initialize accounts from server_config.yaml
        for a in self._config_server['apis']:
            account = AccountEvent()
            account.account_id = self._config_server[a]['userid']
            account.api = self._config_server[a]['api']
            self._account_dict[account.account_id] = account

    def on_account(self, account_event):
        if account_event.account_id in self._account_dict:
            self._account_dict[account_event.account_id].preday_balance = account_event.preday_balance
            self._account_dict[account_event.account_id].balance = account_event.balance
            self._account_dict[account_event.account_id].available = account_event.available
            self._account_dict[account_event.account_id].commission = account_event.commission
            self._account_dict[account_event.account_id].margin = account_event.margin
            self._account_dict[account_event.account_id].closed_pnl = account_event.closed_pnl
            self._account_dict[account_event.account_id].open_pnl = account_event.open_pnl
            self._account_dict[account_event.account_id].timestamp = account_event.timestamp
        else:
            self._account_dict[account_event.account_id] = account_event