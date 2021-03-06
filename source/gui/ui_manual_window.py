#!/usr/bin/env python
# -*- coding: utf-8 -*-
# http://stackoverflow.com/questions/9957195/updating-gui-elements-in-multithreaded-pyqt
import sys
import os
from queue import Queue, Empty
from PyQt5 import QtCore, QtWidgets, QtGui, QtWebEngineWidgets
from datetime import datetime
import requests
import itchat
sys.path.insert(0,"../..")

from source.common.datastruct import *  
from source.common import sqglobal

@itchat.msg_register(itchat.content.TEXT)
def print_content(msg):
    print(msg['Text'])
    strmsg = str(msg['Text'])
    sqglobal.wxcmd = strmsg
    # if strmsg.startswith('!SQ:'):
    #     datastruct.wxcmd = strmsg.split(':')[1]
    #     print(datastruct.wxcmd)

class ManualWindow(QtWidgets.QFrame):
    order_signal = QtCore.pyqtSignal(OrderEvent)
    manual_req = QtCore.pyqtSignal(str)
    subscribe_signal = QtCore.pyqtSignal(SubscribeEvent)
    qryacc_signal = QtCore.pyqtSignal(QryAccEvent) 
    qrypos_signal = QtCore.pyqtSignal(QryPosEvent)    
    qrycontract_signal = QtCore.pyqtSignal(QryContractEvent) 

    def __init__(self, apilist, acclist):
        super(ManualWindow, self).__init__()

        ## member variables
        self._current_time = None
        self._apilist = apilist
        self._acclist = acclist
        self._apistatusdict = {}
        self._widget_dict = {}

        self.manualorderid = 0
        self.init_gui()
        self.wechat = ItchatThread()
        self.init_wxcmd()

    def wxlogin(self):
        itchat.auto_login()
        self.wechat.start()
        
    def sendwxcmd(self,msg):
        self.textbrowser.append(msg)
        if msg.startswith('!SQ:'):
            req = msg.split(':')[1]  
            self.manual_req.emit(req)

    def updatestatus(self,index=0):
        key = self.api_type.currentText() + '.TD.' + self.accounts.currentText()
        apistatus = str(self._apistatusdict[key].name)
        self.apistatus.setText(apistatus)
        
    def updateapistatusdict(self,msg):
        key = msg.source
        if key.endswith('.MD'):
            key = key.replace('.MD','.TD.')
        self._apistatusdict[key] = ESTATE(int(msg.content))
        # print(self._apistatusdict[key].name)
        self.updatestatus()
        pass

    def refresh(self):
        msg2 = '*' \
            + '|' + '0' + '|' + str(MSG_TYPE.MSG_TYPE_ENGINE_STATUS.value)
        self.manual_req.emit(msg2)

    def connect(self):
        msg = self.api_type.currentText() + '.TD.' + self.accounts.currentText() \
            + '|' + '0' + '|' + str(MSG_TYPE.MSG_TYPE_ENGINE_CONNECT.value)
        self.manual_req.emit(msg)
        msg2 = self.api_type.currentText() + '.MD' \
            + '|' + '0' + '|' + str(MSG_TYPE.MSG_TYPE_ENGINE_CONNECT.value)
        self.manual_req.emit(msg2)

    def disconnect(self):
        msg = self.api_type.currentText() + '.TD.' + self.accounts.currentText() \
            + '|' + '0' + '|' + str(MSG_TYPE.MSG_TYPE_ENGINE_DISCONNECT.value)
        self.manual_req.emit(msg)
        msg2 = self.api_type.currentText() + '.MD' \
            + '|' + '0' + '|' + str(MSG_TYPE.MSG_TYPE_ENGINE_DISCONNECT.value)
        self.manual_req.emit(msg2)

    def reset(self):
        msg = self.api_type.currentText() + '.TD.' + self.accounts.currentText() \
            + '|' + '0' + '|' + str(MSG_TYPE.MSG_TYPE_ENGINE_RESET.value)
        self.manual_req.emit(msg)
        msg2 = self.api_type.currentText() + '.MD' \
            + '|' + '0' + '|' + str(MSG_TYPE.MSG_TYPE_ENGINE_RESET.value)
        self.manual_req.emit(msg2)


    def send_cmd(self):
        try:
            cmdstr= str(self.cmd.text())
            self.manual_req.emit(cmdstr)
        except:
            print('send cmd error')

    def subsrcibe(self,ss):
        ss.destination = self.api_type.currentText() + '.MD'
        ss.source = '0'
        self.subscribe_signal.emit(ss)


    def place_order_ctp(self,of):
        try:
            o = OrderEvent()
            o.msg_type = MSG_TYPE.MSG_TYPE_ORDER_CTP
            o.destination = self.api_type.currentText() + '.TD.' + self.accounts.currentText()
            o.source = '0'
            o.api = 'StarQuant' #self.api_type.currentText() 
            o.account = self.accounts.currentText()
            o.clientID = 0
            o.client_order_id = self.manualorderid
            self.manualorderid = self.manualorderid + 1
            # o.create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            o.orderfield = of
            self.order_signal.emit(o)
        except:
            print('place order error')

    def place_order_paper(self,of):
        try:
            o = OrderEvent()
            o.msg_type = MSG_TYPE.MSG_TYPE_ORDER_PAPER
            o.destination = self.api_type.currentText() + '.TD'
            o.source = '0'

            o.api = 'StarQuant' #self.api_type.currentText() 
            o.account = self.accounts.currentText()
            o.clientID = 0
            o.client_order_id = self.manualorderid
            self.manualorderid = self.manualorderid + 1
            # o.create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            o.orderfield = of
            self.order_signal.emit(o)
        except:
            print('place order error')

    def qryacc(self,qa):
        qa.destination = self.api_type.currentText() + '.TD.' + self.accounts.currentText()
        qa.source = '0'
        self.qryacc_signal.emit(qa)

    def qrypos(self,qp):
        qp.destination = self.api_type.currentText() + '.TD.' + self.accounts.currentText()
        qp.source = '0'
        self.qrypos_signal.emit(qp)   

    def qrycontract(self,qc):
        qc.destination = self.api_type.currentText() + '.TD.' + self.accounts.currentText()
        qc.source = '0'
        self.qrycontract_signal.emit(qc)          
     

    def init_wxcmd(self):
        self.wechatmsg = ItchatMsgThread()
        # self.wechatmsg.wechatcmd.connect(self._outgoing_queue.put)
        self.wechatmsg.wechatcmd.connect(self.sendwxcmd)
        self.wechatmsg.start()

    def init_gui(self):
        self.setFrameShape(QtWidgets.QFrame.StyledPanel) 
        manuallayout = QtWidgets.QFormLayout()
        # manuallayout.addRow(QtWidgets.QLabel('Manual Control Center'))

        self.api_type = QtWidgets.QComboBox()
        self.api_type.addItems([str(element) for element in self._apilist])
        self.accounts = QtWidgets.QComboBox()
        al = [str(element) for element in self._acclist]
        al.insert(0,'')
        for api in self._apilist:
            for acc in al:
                key1 = str(api) + '.TD.' + acc
                self._apistatusdict[key1] = ESTATE.STOP
        self.accounts.addItems(al)
        self.apistatus = QtWidgets.QLineEdit()
        self.apistatus.setText('STOP')
        self.apistatus.setReadOnly(True)
        self.api_type.currentIndexChanged.connect(self.updatestatus)
        self.accounts.currentIndexChanged.connect(self.updatestatus)
        self.btn_refresh = QtWidgets.QPushButton('Refresh')
        self.btn_refresh.clicked.connect(self.refresh)

        manualhboxlayout1 = QtWidgets.QHBoxLayout()
        manualhboxlayout1.addWidget(QtWidgets.QLabel('API'))
        manualhboxlayout1.addWidget(self.api_type)
        manualhboxlayout1.addWidget(QtWidgets.QLabel('Account'))
        manualhboxlayout1.addWidget(self.accounts) 
        manualhboxlayout1.addWidget(QtWidgets.QLabel('Status'))  
        manualhboxlayout1.addWidget(self.apistatus)  
        manualhboxlayout1.addWidget(self.btn_refresh)            
        manuallayout.addRow(manualhboxlayout1)   
 
        self.btn_connect = QtWidgets.QPushButton('Connect')
        self.btn_connect.clicked.connect(self.connect)
        self.btn_disconnect = QtWidgets.QPushButton('Logout')
        self.btn_disconnect.clicked.connect(self.disconnect)
        self.btn_reset = QtWidgets.QPushButton('Reset')
        self.btn_reset.clicked.connect(self.reset)

      
        manualhboxlayout2 = QtWidgets.QHBoxLayout()
        manualhboxlayout2.addWidget(self.btn_connect)
        manualhboxlayout2.addWidget(self.btn_disconnect)
        manualhboxlayout2.addWidget(self.btn_reset)
        manuallayout.addRow(manualhboxlayout2) 

        self.btn_cmd = QtWidgets.QPushButton('User-Defined')
        self.btn_cmd.clicked.connect(self.send_cmd)
        self.cmd = QtWidgets.QLineEdit()
        self.cmd.returnPressed.connect(self.send_cmd)
        manualhboxlayout3 = QtWidgets.QHBoxLayout()
        manualhboxlayout3.addWidget(self.btn_cmd)
        manualhboxlayout3.addWidget(self.cmd)
        manuallayout.addRow(manualhboxlayout3)


        self.btn_wx_login = QtWidgets.QPushButton('Login')
        self.btn_wx_logout = QtWidgets.QPushButton('Logout')
        self.btn_wx_login.clicked.connect(self.wxlogin)
        self.btn_wx_logout.clicked.connect(itchat.logout)
        manualhboxlayout4 = QtWidgets.QHBoxLayout()
        manualhboxlayout4.addWidget(QtWidgets.QLabel('Wechat Notify'))
        manualhboxlayout4.addWidget(self.btn_wx_login)
        manualhboxlayout4.addWidget(self.btn_wx_logout)
        manuallayout.addRow(manualhboxlayout4)



        self.textbrowser = QtWidgets.QTextBrowser() 
        manuallayout.addRow(self.textbrowser)  

        self.api_widget = QtWidgets.QStackedWidget() 

        ctpapi = CtpApiWindow()
        ctpapi.subscribe_signal.connect(self.subsrcibe)
        ctpapi.qryacc_signal.connect(self.qryacc)
        ctpapi.qrypos_signal.connect(self.qrypos)
        ctpapi.qrycontract_signal.connect(self.qrycontract)
        ctpapi.orderfield_signal.connect(self.place_order_ctp)

        paperapi = PaperApiWindow()
        paperapi.orderfield_signal.connect(self.place_order_paper)

        self.api_widget.addWidget(ctpapi)
        self.api_widget.addWidget(paperapi)
        self.api_widget.setCurrentIndex(0)
        self.api_type.currentIndexChanged.connect(self.api_widget.setCurrentIndex)
        manuallayout.addRow(self.api_widget)  

        self.logoutput =  QtWidgets.QTextBrowser()
        self.logoutput.setMinimumHeight(600) 
        manuallayout.addRow(self.logoutput)  

        self.setLayout(manuallayout)

class CtpApiWindow(QtWidgets.QFrame):
    orderfield_signal = QtCore.pyqtSignal(CtpOrderField)
    subscribe_signal = QtCore.pyqtSignal(SubscribeEvent)
    qryacc_signal = QtCore.pyqtSignal(QryAccEvent) 
    qrypos_signal = QtCore.pyqtSignal(QryPosEvent)    
    qrycontract_signal = QtCore.pyqtSignal(QryContractEvent) 
    def __init__(self):
        super(CtpApiWindow, self).__init__()
        self.orderfielddict = {}
        self.init_gui()


    def init_gui(self):
        ctpapilayout = QtWidgets.QFormLayout()

        # self.exchange = QtWidgets.QComboBox()
        # self.exchange.addItems(['SHFE','ZCE','DCE','CFFEX','INE'])
        # self.sec_type = QtWidgets.QComboBox()
        # self.sec_type.addItems(['Future', 'Option', 'Combination','Spot'])
        # ctphboxlayout1 = QtWidgets.QHBoxLayout()
        # ctphboxlayout1.addWidget(QtWidgets.QLabel('Exchange'))
        # ctphboxlayout1.addWidget(self.exchange)
        # ctphboxlayout1.addWidget(QtWidgets.QLabel('Security'))
        # ctphboxlayout1.addWidget(self.sec_type) 
        # ctpapilayout.addRow(ctphboxlayout1)       
 
        self.qry_type = QtWidgets.QComboBox()
        self.qry_type.addItems(['Account','Position','Contract'])
        self.qry_content =  QtWidgets.QLineEdit()
        self.btn_qry = QtWidgets.QPushButton('QUERY')
        self.btn_qry.clicked.connect(self.qry)
        ctphboxlayout0 = QtWidgets.QHBoxLayout()
        ctphboxlayout0.addWidget(QtWidgets.QLabel('Query Type'))
        ctphboxlayout0.addWidget(self.qry_type)
        ctphboxlayout0.addWidget(self.qry_content)
        ctphboxlayout0.addWidget(self.btn_qry) 
        ctpapilayout.addRow(ctphboxlayout0)   

        self.sym = QtWidgets.QLineEdit()
        self.sym.returnPressed.connect(self.subscribe)  # subscribe market data
        self.order_ref = QtWidgets.QLineEdit()
        ctphboxlayout3 = QtWidgets.QHBoxLayout()
        ctphboxlayout3.addWidget(QtWidgets.QLabel('InstrumentID'))
        ctphboxlayout3.addWidget(self.sym)
        ctphboxlayout3.addWidget(QtWidgets.QLabel('OrderRef'))
        ctphboxlayout3.addWidget(self.order_ref) 
        ctpapilayout.addRow(ctphboxlayout3)       

        self.hedge_type = QtWidgets.QComboBox()
        self.hedge_type.addItems(['Speculation','Arbitrage','Hedge','MarketMaker','SpecHedge','HedgeSpec'])
        self.orderfielddict['hedge'] = ['1','2','3','5','6','7']
        self.direction_type = QtWidgets.QComboBox()
        self.direction_type.addItems(['Net', 'Long','Short'])
        self.orderfielddict['direction'] = ['1','2','3']
        self.order_flag_type = QtWidgets.QComboBox()
        self.order_flag_type.addItems(['Open', 'Close', 'Force_Close','Close_Today','Close_Yesterday', 'Force_Off','Local_Forceclose'])
        self.orderfielddict['orderflag'] = ['0','1','2','3','4','5','6']
        ctphboxlayout4 = QtWidgets.QHBoxLayout()
        ctphboxlayout4.addWidget(QtWidgets.QLabel('Hedge'))
        ctphboxlayout4.addWidget(self.hedge_type)         
        ctphboxlayout4.addWidget(QtWidgets.QLabel('Direction'))
        ctphboxlayout4.addWidget(self.direction_type)
        ctphboxlayout4.addWidget(QtWidgets.QLabel('OrderFlag'))
        ctphboxlayout4.addWidget(self.order_flag_type) 
        ctpapilayout.addRow(ctphboxlayout4)        


        self.order_price_type = QtWidgets.QComboBox()
        self.order_price_type.addItems(['AnyPrice','LimitPrice','BestPrice','LastPrice','AskPrice1','BidPrice1'])
        self.orderfielddict['pricetype'] = ['1','2','3','4','8','C']
        self.limit_price = QtWidgets.QLineEdit()
        self.limit_price.setValidator(QtGui.QDoubleValidator())
        self.limit_price.setText('0')
        ctphboxlayout5 = QtWidgets.QHBoxLayout()
        ctphboxlayout5.addWidget(QtWidgets.QLabel('PriceType'))
        ctphboxlayout5.addWidget(self.order_price_type)
        ctphboxlayout5.addWidget(QtWidgets.QLabel('LimitPrice'))
        ctphboxlayout5.addWidget(self.limit_price) 
        ctpapilayout.addRow(ctphboxlayout5)      


        self.order_quantity = QtWidgets.QLineEdit()
        self.order_quantity.setValidator(QtGui.QIntValidator())
        self.order_quantity.setText('0')
        self.order_minquantity = QtWidgets.QLineEdit()
        self.order_minquantity.setValidator(QtGui.QIntValidator())
        self.order_minquantity.setText('0')
        ctphboxlayout6 = QtWidgets.QHBoxLayout()
        ctphboxlayout6.addWidget(QtWidgets.QLabel('Volume'))
        ctphboxlayout6.addWidget(self.order_quantity)
        ctphboxlayout6.addWidget(QtWidgets.QLabel('MinVolume'))
        ctphboxlayout6.addWidget(self.order_minquantity) 
        ctpapilayout.addRow(ctphboxlayout6)      


        self.order_condition_type = QtWidgets.QComboBox()
        self.order_condition_type.addItems(['Immediately','Touch','TouchProfit','ParkedOrder','LastPriceGreater','LastPriceLesser'])
        self.orderfielddict['condition'] = ['1','2','3','4','5','7']
        self.stop_price = QtWidgets.QLineEdit()
        self.stop_price.setValidator(QtGui.QDoubleValidator())
        self.stop_price.setText('0.0')
        ctphboxlayout7 = QtWidgets.QHBoxLayout()
        ctphboxlayout7.addWidget(QtWidgets.QLabel('Condition'))
        ctphboxlayout7.addWidget(self.order_condition_type)
        ctphboxlayout7.addWidget(QtWidgets.QLabel('StopPrice'))
        ctphboxlayout7.addWidget(self.stop_price) 
        ctpapilayout.addRow(ctphboxlayout7)      


        self.time_condition_type = QtWidgets.QComboBox()
        self.time_condition_type.addItems(['IOC','GFS','GFD','GTD','GTC','GFA'])
        self.orderfielddict['timecondition'] = ['1','2','3','4','5','6']
        self.time_condition_time = QtWidgets.QLineEdit()
        self.volume_condition_type = QtWidgets.QComboBox()
        self.volume_condition_type.addItems(['Any','Min','Total'])
        self.orderfielddict['volumecondition'] = ['1','2','3']
        ctphboxlayout8 = QtWidgets.QHBoxLayout()
        ctphboxlayout8.addWidget(QtWidgets.QLabel('TimeCondition'))
        ctphboxlayout8.addWidget(self.time_condition_type)
        ctphboxlayout8.addWidget(self.time_condition_time)
        ctphboxlayout8.addWidget(QtWidgets.QLabel('VolumeCondition'))
        ctphboxlayout8.addWidget(self.volume_condition_type) 
        ctpapilayout.addRow(ctphboxlayout8)      

        # self.ordertag = QtWidgets.QLineEdit()
        # ctpapilayout.addRow(self.ordertag)

        # self.option_type = QtWidgets.QComboBox()
        # self.option_type.addItems(['Call','Put'])


        # ctpapilayout.addRow(self.btn_request)
        self.request_type = QtWidgets.QComboBox()
        self.request_type.addItems(['Order','ParkedOrder','OrderAction','ParkedOrderAction','ExecOrder','ExecOrderAction','ForQuote','Quote','QuoteAction','OptionSelfClose','OptionSelfCloseAction','CombActionInsert'])
        self.algo_type = QtWidgets.QComboBox()
        self.algo_type.addItems(['None','TWAP','Iceberg','Sniper'])

        ctphboxlayout2 = QtWidgets.QHBoxLayout()
        ctphboxlayout2.addWidget(QtWidgets.QLabel('Request Type'))
        ctphboxlayout2.addWidget(self.request_type)
        ctphboxlayout2.addWidget(QtWidgets.QLabel('Algo-trading Option'))        
        ctphboxlayout2.addWidget(self.algo_type)        
        ctpapilayout.addRow(ctphboxlayout2)  

        self.algoswidgets = QtWidgets.QStackedWidget()
        ctpapilayout.addRow(self.algoswidgets) 

        self.btn_request = QtWidgets.QPushButton('REQUEST')
        self.btn_request.clicked.connect(self.generate_request)     # insert order
        ctpapilayout.addRow(self.btn_request)




        self.setLayout(ctpapilayout)

    def qry(self):
        if(self.qry_type.currentText() == 'Account'):
            qa = QryAccEvent()
            self.qryacc_signal.emit(qa)
            return
        if (self.qry_type.currentText() == 'Position'):
            qp = QryPosEvent()
            self.qrypos_signal.emit(qp)
            return
        if (self.qry_type.currentText() == 'Contract'):
            qp = QryContractEvent()
            qp.sym_type = SYMBOL_TYPE.CTP
            qp.content = self.qry_content.text()
            self.qrycontract_signal.emit(qp)
            return

    def generate_request(self):
        print("ctp request at ", datetime.now())
        if (self.request_type.currentText() =='Order'):
            of = CtpOrderField()
            of.InstrumentID = self.sym.text()
            of.OrderPriceType = self.orderfielddict['pricetype'][self.order_price_type.currentIndex()]
            of.Direction = self.orderfielddict['direction'][self.direction_type.currentIndex()]
            of.CombOffsetFlag = self.orderfielddict['orderflag'][self.order_flag_type.currentIndex()]
            of.CombHedgeFlag = self.orderfielddict['hedge'][self.hedge_type.currentIndex()]
            of.TimeCondition = self.orderfielddict['timecondition'][self.time_condition_type.currentIndex()]
            of.GTDDate = self.time_condition_time.text()
            of.VolumeCondition = self.orderfielddict['volumecondition'][self.volume_condition_type.currentIndex()]
            of.ContingentCondition = self.orderfielddict['condition'][self.order_condition_type.currentIndex()]
            of.ForceCloseReason = '0'
            of.IsAutoSuspend = 0
            of.UserForceClose = 0
            try:
                of.LimitPrice = float(self.limit_price.text())
                of.VolumeTotalOriginal = int(self.order_quantity.text())
                of.MinVolume = int(self.order_minquantity.text())
                of.StopPrice = float(self.stop_price.text())
            except:
                pass
            
            self.orderfield_signal.emit(of)
            return

    def subscribe(self):
        ss = SubscribeEvent()
        ss.sym_type = SYMBOL_TYPE.CTP
        ss.content = str(self.sym.text())
        self.subscribe_signal.emit()
        return
        



class PaperApiWindow(QtWidgets.QFrame):
    orderfield_signal = QtCore.pyqtSignal(PaperOrderField)

    def __init__(self):
        super(PaperApiWindow, self).__init__()
        self.orderfielddict = {}
        self.init_gui()

    def init_gui(self):
        paperapilayout = QtWidgets.QFormLayout()

        self.exchange = QtWidgets.QComboBox()
        self.exchange.addItems(['SHFE','ZCE','DCE','CFFEX','INE'])
        self.orderfielddict['exchange'] = ['SHFE','ZCE','DCE','CFFEX','INE']
        self.sec_type = QtWidgets.QComboBox()
        self.sec_type.addItems(['F', 'O', 'C','S'])
        self.orderfielddict['sectype'] = ['F','O','C','S']
        paperhboxlayout1 = QtWidgets.QHBoxLayout()
        paperhboxlayout1.addWidget(QtWidgets.QLabel('Exchange'))
        paperhboxlayout1.addWidget(self.exchange)
        paperhboxlayout1.addWidget(QtWidgets.QLabel('Security'))
        paperhboxlayout1.addWidget(self.sec_type) 
        paperapilayout.addRow(paperhboxlayout1) 

        self.sym = QtWidgets.QLineEdit()
        self.sym_no = QtWidgets.QLineEdit()
        paperhboxlayout2 = QtWidgets.QHBoxLayout()
        paperhboxlayout2.addWidget(QtWidgets.QLabel('SymbolName'))
        paperhboxlayout2.addWidget(self.sym)
        paperhboxlayout2.addWidget(QtWidgets.QLabel('SymbolNo'))
        paperhboxlayout2.addWidget(self.sym_no) 
        paperapilayout.addRow(paperhboxlayout2) 

        self.order_type = QtWidgets.QComboBox()
        self.order_type.addItems(['MKT', 'LMT', 'STP','STPLMT','FAK', 'FOK'])
        self.orderfielddict['ordertype'] = [OrderType.MKT,OrderType.LMT,OrderType.STP,OrderType.STPLMT,OrderType.FAK,OrderType.FOK]
        self.direction = QtWidgets.QComboBox()
        self.direction.addItems(['Long', 'Short'])
        self.orderfielddict['direction'] = [1,-1]
        self.order_flag = QtWidgets.QComboBox()
        self.order_flag.addItems(['Open', 'Close', 'Close_Today','Close_Yesterday'])
        self.orderfielddict['orderflag'] = [OrderFlag.OPEN,OrderFlag.CLOSE,OrderFlag.CLOSE_TODAY,OrderFlag.CLOSE_YESTERDAY]
        paperhboxlayout3 = QtWidgets.QHBoxLayout()
        paperhboxlayout3.addWidget(QtWidgets.QLabel('Order Type'))
        paperhboxlayout3.addWidget(self.order_type)
        paperhboxlayout3.addWidget(QtWidgets.QLabel('Direction'))
        paperhboxlayout3.addWidget(self.direction) 
        paperhboxlayout3.addWidget(QtWidgets.QLabel('Order Flag'))
        paperhboxlayout3.addWidget(self.order_flag)         
        paperapilayout.addRow(paperhboxlayout3)         

        self.limit_price = QtWidgets.QLineEdit()
        self.limit_price.setValidator(QtGui.QDoubleValidator())
        self.limit_price.setText('0.0')
        self.stop_price = QtWidgets.QLineEdit()
        self.stop_price.setText('0.0')
        self.stop_price.setValidator(QtGui.QDoubleValidator())
        self.order_quantity = QtWidgets.QLineEdit()
        self.order_quantity.setValidator(QtGui.QIntValidator())
        self.order_quantity.setText('0')
        paperhboxlayout4 = QtWidgets.QHBoxLayout()
        paperhboxlayout4.addWidget(QtWidgets.QLabel('LimitPrice'))
        paperhboxlayout4.addWidget(self.limit_price)
        paperhboxlayout4.addWidget(QtWidgets.QLabel('StopPrice'))
        paperhboxlayout4.addWidget(self.stop_price)        
        paperhboxlayout4.addWidget(QtWidgets.QLabel('Quantity'))
        paperhboxlayout4.addWidget(self.order_quantity) 
        paperapilayout.addRow(paperhboxlayout4) 

        self.btn_order = QtWidgets.QPushButton('Place_Order')
        self.btn_order.clicked.connect(self.place_order)     # insert order

        paperapilayout.addRow(self.btn_order)  

        self.setLayout(paperapilayout)

    def place_order(self): 
            fullname = self.exchange.currentText() + ' ' + self.sec_type.currentText() + ' ' + self.sym.text() + ' ' + self.sym_no.text()       
            o = PaperOrderField()
            o.full_symbol = fullname
            o.order_type = self.orderfielddict['ordertype'][self.order_type.currentIndex()]
            o.order_flag = self.orderfielddict['orderflag'][self.order_flag.currentIndex()]
            try:
                o.order_size = int(self.order_quantity.text())* self.orderfielddict['direction'][self.direction.currentIndex()]
                o.limit_price = float(self.limit_price.text())
                o.stop_price = float(self.stop_price.text())
            except:
                pass
            self.orderfield_signal.emit(o)



class ItchatThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
    def run(self):
        itchat.run()




class ItchatMsgThread(QtCore.QThread):
    wechatcmd = QtCore.pyqtSignal(str)
    def __init__(self):
        QtCore.QThread.__init__(self)
    def run(self):
        while True:
            if (sqglobal.wxcmd):
                print(sqglobal.wxcmd)
                self.wechatcmd.emit(sqglobal.wxcmd)
                sqglobal.wxcmd = ''
            self.sleep(1)
        


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    apilist = ['CTP','PAPER']
    acclist = ['0120000963','99683265']
    ui = ManualWindow(apilist,acclist)
    ui.show()
    app.exec_()