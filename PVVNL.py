# Python Inbuilt Functions
import re
import base64
import datetime
import pdfplumber
import os, shutil
from base64 import b64decode
import pdfplumber
import io
import pyodbc
import smtplib
import openpyxl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
import random
import math
import requests
import json
from base64 import b64decode
import base64
import psycopg2
from requests.auth import HTTPBasicAuth
import textract
import tabula
from xlsxwriter.workbook import Workbook
from openpyxl import load_workbook
import csv
# Developed Functions
from func_call.api_post import call_api
from func_call.call_db import call_db_post
from func_call.indus_key import get_indus_id
from func_call.mapping_api import api_mapping
from func_call.fields_checker import date_checker, check_api_call
from func_call.pdf_parser import data_extractor_numbers, data_extractor_alphanumeric, data_extractor_string
from func_call.fields_checker import date_checker, bill_no_check, Meter_reading_check, reading_date_check, check_range, \
    check_api_call



def get_validation(dic1):
    output = {"AccountNumber": bill_no_check(dic1.get("AccountNumber"), 12),
              #"BillNumber": bill_no_check(dic1.get("BillNumber"), 16),#26.05.2021
              # "MeterNumber" :bill_no_check(dic1.get("MeterNumber"),8),
              # "IndusID" :bill_no_check(dic1.get("IndusSiteID"),10),
              "KWH Reading Check": Meter_reading_check(dic1.get("KWHStartReading"), dic1.get("KWHEndReading")),
              "KVAH Reading Check": Meter_reading_check(dic1.get("KVAHStartReading"), dic1.get("KVAHEndReading")),
              "Reading_Date_Check": reading_date_check(dic1.get("StartDate"), dic1.get('EndDate')),
              "Due_Date_Check": reading_date_check(dic1.get("BillingDate"), dic1.get('DueDate')),
              ##              "PowerFactor" : check_range(dic1.get("PowerFactor"), 1.00),
              ##              "MaximumDemand" : check_range(dic1.get("MaximumDemand"), 100),
              ##              "EnergyCharges" : check_range(dic1.get("EnergyCharges"), 200000.00),
              ##              "FixedCharges" : check_range(dic1.get("FixedCharges"), 200000.00),
              ##              "PPACCharges" : check_range(dic1.get("PPACCharges"), 200000.00),
              ##              "ArrearAmount1" : check_range(dic1.get("ArrearAmount1"),200000.00),
              ##              "CurrentBillLPSC" : check_range(dic1.get("CurrentBillLPSC"), 200000.00),
              ##              "InterestonDeposit" : check_range(dic1.get("InterestonDeposit"), 200000.00),
              ##              "TaxonInterestonDeposit" : check_range(dic1.get("TaxonInterestonDeposit"), 200000.00),
              ##              "TaxesandDuties" : check_range(dic1.get("TaxesandDuties"), 200000.00),
              ##              "ElectricitySurcharge" : check_range(dic1.get("ElectricitySurcharge"), 200000.00),
              ##              "EBAmountBeforeDue" : check_range(dic1.get("EBAmountBeforeDue"), 2000000.00),
              ##              "RebateAmount" : check_range(dic1.get("RebateAmount"), 100000.00),
              }
    return output




def trigger_tpdl(path, file_name):
    start_t = datetime.datetime.now()
    with pdfplumber.open(path) as pdf:    
        page = pdf.pages[0]
        page1 = pdf.pages[0]
        text3 = page.extract_text()
        text4 = page1.extract_text()
        text = text3 #+ text4
    data_dict = {}
    l = ['(', ')', '.', '/', '-']
    print(text)

    
    # Account No
    acc_no = data_extractor_numbers(text, 'Months',data_dict, 'Meter', 'Account No', l, '\d{12}', -2)

    # For Bill Date
    bill_date = data_extractor_numbers(text, 'Bill Date',data_dict, 'Security', 'Billing Date', l,
                                       '\d{2}/\d{2}/\d{4}', 0)
    data_dict['Bill Date'] = date_checker(bill_date, "%d/%m/%Y")

    # For Due Date
    due_date = data_extractor_numbers(text, 'Bill Date',data_dict, 'Security', 'Due Date', l, '\d{2}/\d{2}/\d{4}',
                                      1)
    data_dict['Due_date'] = date_checker(due_date, "%d/%m/%Y")

    # For Disconnection Date
    disconnection_date = data_extractor_numbers(text, 'Disconnection Date',data_dict, 'Bill Details Amount',
                                                'Disconnection Date', l, '\d{2}/\d{2}/\d{4}', 0)
    data_dict['DisconnectionDate'] = date_checker(disconnection_date, "%d/%m/%Y")

    data_dict['DISCOMEntryDate'] = ''

    # For Meter Start Date
    from_date = data_extractor_alphanumeric(text, 'From To Months',data_dict, 'Multiplying Consumed', 'Start Date',
                                            l, '\d{2}\/\d{2}\/\d{4}', 1)
    data_dict['StartDate'] = date_checker(from_date, "%d/%m/%Y")

    # For Meter End Date
    to_date = data_extractor_alphanumeric(text, 'From To Months',data_dict, 'Multiplying Consumed', 'End Date', l,
                                          '\d{2}\/\d{2}\/\d{4}', 2)
    data_dict['EndDate'] = date_checker(to_date, "%d/%m/%Y")
    #print(data_dict)
    # Power Factor
    pf = data_extractor_numbers(text, 'Due Date',data_dict, 'Security', 'Power Factor', l, '\d+\.\d+', -2)

    # Maximum Demand
    data_extractor_numbers(text, 'Due Date',data_dict, 'Security', 'MaximumDemand', l, '\d+\.\d+', -1)

    # BillType
    bill_base = data_extractor_alphanumeric(text, 'Disconnection Date',data_dict, 'Bill Details Amount', 'BillUnits', l, '','').split("Amount")[1]
    bill_base = bill_base.split(" ")[0]
    # print(bill_base)
    if "MU" in bill_base or "OK" in bill_base or "BR" in bill_base:
        bill_type = "Normal EB"
        meter_complexity = "Normal"
    else:
        if "PROV" in bill_base:
            bill_type = "Abnormal EB"
            meter_complexity = "Average Bill"
        elif "CDF" in bill_base or "CEILL" in bill_base or "IDF" in bill_base or "ASS" in bill_base or "RDF" in bill_base or "ADF" in bill_base:
            bill_type = "Abnormal EB"
            meter_complexity = "Meter Faulty"
        elif "NR" in bill_base or "UDC" in bill_base or "NA" in bill_base:
            bill_type = "Abnormal EB"
            meter_complexity = "Door Lock"
    data_dict['BillType'] = bill_type
    data_dict['MeterComplexity'] = meter_complexity



##    # Bill Number
##
##    bill_no = data_extractor_alphanumeric(text, 'Months', data_dict, 'Meter', 'Bill No', l, '','')
##    billno_1=bill_no.replace(from_date,'')
##    billno_2=billno_1.replace(to_date,'')
##    billno_final=billno_2.split()[9]
##    print(billno_final)
##    data_dict['Bill No']=billno_final

    # Bill Number#17.05.2021

    bill_no = data_extractor_alphanumeric(text, 'Months', data_dict, 'Meter', 'Bill No', l, '','')
    print(bill_no)
    billno_1=bill_no.replace(from_date,'')
    billno_2=billno_1.replace(to_date,'')
    print(billno_2)
    billno_2 = billno_2.replace("Last Current Multiplying Consumed Power Actual",'')#17.05.2021
    billno_2 = billno_2.replace("Last Current Multiplying Consumed Power",'')#17.05.2021
    billno_final=billno_2.split()[-2]#17.05.2021
    if "/" in str( billno_final):
        billno_final=billno_2.split()[-3]
    else:
        billno_final=billno_2.split()[-2]
    print(billno_final)
    data_dict['Bill No']=billno_final


    # BilledUnit
    bill_unit = data_extractor_numbers(text, 'Disconnection Date',data_dict, 'Bill Details Amount', 'BilledUnits', l,'\d+\.\d+|\d+', 2)
    data_dict['BilledUnit'] = bill_unit

    # EnergyCharges
    val1=data_extractor_numbers(text, 'Energy Charges',data_dict, 'Fixed/Demand', 'EnergyCharges1', l, '\d+\.\d{2}|\d+',0)
    val2=data_extractor_numbers(text,'Minimum Charges',data_dict,'\n','MinimumCharges1',l,'\d+\.\d+|\d+',0)
    energycharges = "{0:.2f}".format(float(val1) + float(val2))
    data_dict['EnergyCharges'] = energycharges


    # FixedCharges
    fc = data_extractor_numbers(text, 'Fixed/Demand Charges',data_dict, '. Arrears', 'Fixed Charges', l, '', '')
    fc = fc.split("/")
    print(fc)
    data_dict['Fixed Charges'] = fc[0]
    data_dict['DemandCharges'] = fc[1]

    data_dict['FuelSurcharge'] = ''
    data_dict['PPACCharges'] = ''
    data_dict['DevelopmentCharges'] = ''
    data_dict['MiscellaneousCharges'] = '0'

    # CurrentBillLPSC
    data_extractor_numbers(text, 'Current Component',data_dict, '\n', 'CurrentBillLPSC', l, '\d+\.\d+', 0)

    # ArrearLPSC
    arrear_lpsc = data_extractor_numbers(text, 'Arrear Component',data_dict, '\n', 'ArrearLPSC1', l, '\d+\.\d+', 0)
    surcharge=data_extractor_numbers(text,'Energy Arrear',data_dict,'Bill Processor Name','surcharge',l,'','')
    surcharge1=surcharge.split()[-1]
    final_value_arrearlpsc = "{0:.2f}".format(float(arrear_lpsc) + float(surcharge1))
    data_dict['ArrearLPSC'] = final_value_arrearlpsc
    
    
    #DEBIT 
    d=data_extractor_numbers(text,'Assesment / CCBR Adjustments',data_dict,'22. Total Payable Amt','d1',l,'','')
    d=d.replace('()','').split('/')
    d1=d[0].strip()
    d11=d[1].strip()
    d2=data_extractor_numbers(text,'Meter Charges',data_dict,'20. ASD Amount','d2',l,'\-\d+\.\d{,2}|\d+\.\d{,2}',0)
    d3=data_extractor_numbers(text,'D/R Fee',data_dict,'\n','d3',l,'\-\d+\.\d{,2}|\d+\.\d{,2}',0)
    d4=data_extractor_numbers(text,'Others',data_dict,'\n','d4',l,'\-\d+\.\d{,2}|\d+\.\d{,2}',0)
    debit = float(d1)+float(d11)+float(d2)+float(d3)+float(d4)
    
    #Energy Arrear
    energyarrear_0 = data_extractor_numbers(text, 'Energy Arrear', data_dict, '\n', 'energyarrear', l,'\-\d+\.\d+|\d+\.\d+', -1)
    
    #Previous Arrear - Arrear Amount 1
    previous_arrear_0 = data_extractor_numbers(text,'Previous Arrears / Arrear Count',data_dict,'\n','Previous Arrear',l,'\S+',0)
    
    if '-' in previous_arrear_0:
        previous_arrear_0 = 0
    else:
        previous_arrear_0 = previous_arrear_0
    
    if "-" in energyarrear_0:
        energyarrear = previous_arrear_0
    if energyarrear_0 > '10.00' :
        energyarrear = energyarrear_0
    else:
        energyarrear = 0 

    #Arrear Amount1
    Arrear_amount1 = float(debit) + float(energyarrear)
    data_dict['ArrearAmount1'] = Arrear_amount1   
        
    #Other Dues - For Arrear Amount 2
    Other_dues_0 = data_extractor_numbers(text,'16. Other Dues',data_dict,'\n','Other Dues',l,'\-\d+.\d+|\d+.\d+',0)
    Other_dues_0 = str(Other_dues_0)
    Other_dues_1 = data_extractor_numbers(text,'16. Other Dues/ Pending May FC/',data_dict,'0) FC Waiver','Other Dues',l,'\-\d+.\d+|\d+.\d+',0)
    

    if '-' in Other_dues_0:
        Arrear_amount_2 = 0
    else:
        Arrear_amount_2 = Other_dues_0 
        
    if Arrear_amount_2 == '0':
        Arrear_amount2 = Other_dues_1
    else:
        Arrear_amount2 = Arrear_amount_2
        
    data_dict['ArrearAmount2'] = Arrear_amount2
    
    
    #Arrear Amount3
    pending_mayFC = data_extractor_numbers(text,'Pending May FC/',data_dict,' ','pending_may_FC',l,'\d+\.\d+',1)
    
    data_dict['ArrearAmount3'] = pending_mayFC
    
    # For Credit
    c1=data_extractor_numbers(text,'Progressive / CCBR Adjustments',data_dict,'\n','c1',l,'','')
    c1=c1.split()[-1]
    final_c1=c1.split('/')
    c2=data_extractor_numbers(text,'Others / Energy Rebate/Subsidy',data_dict,'Energy Arrear','c2',l,'','')
    c2=c2.split()[-1]
    final_c2=c2.split('/')
    a=final_c1[0]
    b=final_c1[1]
    c=final_c2[0]
    d=final_c2[1]
    e=final_c2[2]
    credit = float(a)+float(b)+float(c)+float(d)+float(e)
    
    #Other Dues - For Refund Amount
    other_dues_a = data_extractor_numbers(text,'Other Dues',data_dict,'\n','Other Dues',l,'\-\d+.\d+|\d+.\d+',0)
    other_dues_a = str(other_dues_a)
    print('other')
    other_dues_b = data_extractor_numbers(text,'Other Dues',data_dict,'\n','Other Dues',l,'\d+.\d+',0)
    
    if '-' in other_dues_a:
        Other_dues_refund = other_dues_a
    else:
        Other_dues_refund = 0
        
        
    if Other_dues_refund == 0:
        Other_dues_refund = other_dues_b
    else:
        Other_dues_refund = Other_dues_refund
    
    Other_dues_refund = str(Other_dues_refund)
        
    if '-' in Other_dues_refund:
        Other_dues_refund = Other_dues_refund
    else:
        Other_dues_refund = 0
        
    Other_dues_refund = str(Other_dues_refund)    
    Other_dues_refund = Other_dues_refund.replace('-','')
        
      
    # Previous Arrears - For refund Amount
    previous_arrear = data_extractor_numbers(text,'Previous Arrears / Arrear Count',data_dict,'\n','Previous Arrear',l,'\S+',0)
    
    if '-' in previous_arrear:
        Previous_Arrear = previous_arrear
    else:
        Previous_Arrear = 0
        
    Previous_Arrear = str(Previous_Arrear)    
    Previous_Arrear = Previous_Arrear.replace('-','')
        
    #Refund For Customer
    refund_for_customer = float(credit) +float(Other_dues_refund)+float(Previous_Arrear)
    
    data_dict['RefundAmountforCustomer'] = '0'
    data_dict['OtherRefund'] = refund_for_customer
    
    
    data_dict['ArrearStartDate1'] = ''
    data_dict['ArrearEndDate1'] = ''
    data_dict['ArrearStartDate2'] = ''
    data_dict['ArrearEndDate2'] = ''
    data_dict['ArrearStartDate3'] = ''
    data_dict['ArrearEndDate3'] = ''
    data_dict['ArrearType1'] = ''
    data_dict['ArrearType2'] = ''
    data_dict['ArrearType3'] = ''
    data_dict['InstallmentNumber1'] = ''
    data_dict['InstallmentNumber2'] = ''
    data_dict['InstallmentNumber3'] = ''
    data_dict['ArrearRemarks1'] = ''
    data_dict['ArrearRemarks2'] = ''
    data_dict['ArrearRemarks3'] = ''

    # PowerFactorPenalty
    pfp = data_extractor_numbers(text, 'Capacitor / LPF Surcharge',data_dict, 'ii) Installment No','PowerFactorPenalty', l, '\d+\.\d+ / \d+\.\d+', 0)
    powerfactor=pfp.split('/')
    value1=powerfactor[0]
    value2=powerfactor[1]
    final_value="{0:.2f}".format(float(value1) + float(value2))
    data_dict['PowerFactorPenalty']=final_value

    # Regualtory Surcharge
    regulatory1=data_extractor_numbers(text,'Regulatory Surcharge 1 :',data_dict,'i) Current Component','Regulatory1',l,'\d+\.\d+',0)
    regulatory2=data_extractor_numbers(text,'Regulatory Surcharge 2 :',data_dict,'ii) Arrear Component','Regulatory2',l,'\d+\.\d+',0)
    regulatorycharges="{0:.2f}".format(float(regulatory1) + float(regulatory2))
    data_dict['RegulatoryCharges']=regulatorycharges

    data_dict['VCRPenalty'] = '0'
    data_dict['TheftandManipulations'] = '0'

    # MDISanctionLoadPenalty
    data_extractor_numbers(text, 'Excess Load/Demand Penality',data_dict, 'i) Bill No', 'MDISanctionLoadPenalty', l,'\d+\.\d+', 0)

    data_dict['OtherPenalty'] = '0'
    data_dict['TaxonInterestonDeposit'] = '0'

    # InterestonDeposit
    iod = data_extractor_numbers(text, 'Temporary (ISD Interest ) / Solar Rebate  (-)',data_dict, '\n','InterestonDeposit', l, '', '')
    iod1 = iod.split('/')[0].strip()
    data_dict['InterestonDeposit'] = iod1

    # PromptPaymentRebate
    data_extractor_numbers(text, 'Rebate Given',data_dict, '\n', 'PromptPaymentRebate', l, '\d+\.\d{2}|\d+', 0)

    # Taxes and Duties
    data_extractor_numbers(text, 'Electricity Duty',data_dict, 'iii) Payable Date', 'TaxesandDuties', l,'\d+\.\d{2}|\d+', 0)

    # EBAmountBeforeDue
    data_extractor_numbers(text, 'Total Payable Amt. On or',data_dict, '\n', 'EBAmountBeforeDue', l,'\d+\.\d+|\d+', 0)

    # EBAmountAfterDue
    data_extractor_numbers(text, 'Total Payable Amount',data_dict, '\n', 'EBAmountAfterDue', l, '\d+\.\d+|\d+', 0)
    
    #RebateAmount
    rebate_amt = data_extractor_numbers(text, 'Pending May FC/', data_dict,'A) PLC Charges', 'RebateAmount',l, '\S+\.\d{2}', -1)
    rebate_amt = str(rebate_amt)
    rebate_amt = rebate_amt.replace('-','')
    data_dict['RebateAmount'] = rebate_amt
    
    
    data_dict['EBAmountFinal'] = '0'
    data_dict['MeterReplacementCharges'] = '0'
    data_dict['GovernmentDuty'] = '0'
    data_dict['ElectricitySurcharge'] = '0'
    data_dict['IGST'] = '0'
    data_dict['SGST'] = '0'
    data_dict['CGST'] = '0'
    data_dict['AdditionalSecurityDepositAmount'] ='0'
    # Security Deposite as per bill
    data_extractor_numbers(text, 'Disconnection Date',data_dict, 'Bill Details Amount', 'EBSDAmount', l,'\d+\.\d+|\d+', -4)

    # Sanction Load
    load= data_extractor_numbers(text,'From To Months',data_dict,'Current','SanctionLoad1',l,'','')
    load=load.split()
    if len(load)==10:
        data_dict['Sanction Load']=load[-3]
    elif len(load)==11:
        data_dict['Sanction Load']=load[-4]

    data_dict['SecurityRefund'] = '0'
    data_dict['PenaltyRefund']=''
    data_dict['RoundOffAmount'] = ''

    data_dict['RoundOffRefund'] = ''
    data_dict['SecurityRemarks'] = ''
    data_dict['PenaltyRemarks'] = ''
    data_dict['DifferenceReasonRemarks'] = ''
    data_dict['EBDifferenceReason'] = ''
    data_dict['CustomerRefundStartDate'] = ''
    data_dict['CustomerRefundEndDate'] = ''
    data_dict['RefundAmountforIndus'] = '0'
    data_dict['IndusRefundStartDate'] = ''
    data_dict['IndusRefundEndDate'] = ''
    data_dict['RefundRemarks'] = ''
    data_dict['UserId'] = 'SS.AUTOMATION'
    data_dict['PPDDate'] = ''

    try:
        with pdfplumber.open(path) as pdf:
            d = []
            pages = pdf.pages
            for i, pg in enumerate(pages):
                data = pages[0].extract_table()#17.05.2021
                # print(data)
                d = data + d
            for x1, xy in enumerate(d):
                # print(d)
                final_val = []
                for val in xy:
                    if val != None:
                        final_val.append(val)
                #print("..",final_val)
                if "Meter No." in str(final_val[0]) and len(final_val) > 2 or "Meter\nNo." in str(final_val[0]) and len(
                        final_val) > 2:
                    value1 = d[x1 + 1]
                    #print("ccc",value1)
                    value2 = []
                    for val in value1:
                        if val != None:
                            value2.append(val)
                    #print(value2[0])
                    data_dict['Meter Number'] = value2[0].strip()

                    a = value2[1].split("/")
                    #print(a)
                    data_dict['From_reading_kwh'] = a[0].strip()
                    data_dict['From_reading_KVAH'] = a[1].strip()

                    b = value2[2].split("/")
                    #print(b)
                    data_dict['To_reading_kwh'] = b[0].strip()
                    data_dict['To_reading_KVAH'] = b[1].strip()
    except:
        values = data_extractor_numbers(text, 'Factor Demand',data_dict, 'Alotted Units', 'Values', l, '','')
        values = values.split()
        read1=values[2]
        p1=read1[:len(read1)//2]
        p2=read1[len(read1)//2:]
        read2=values[0]
        p3=read2[:7]
        p4=read2.replace(p3,'')
        if len(p4)==len(p1):
            data_dict['From_reading_kwh'] = p4
            data_dict['Meter Number'] = p3.strip()
        else:
            p3 = read2[:8]
            p4 = read2.replace(p3, '')
            data_dict['From_reading_kwh'] = p4
            data_dict['Meter Number'] = p3.strip()
        # print(p3)
        # print(p4)
        data_dict['From_reading_KVAH'] = p1
        data_dict['To_reading_kwh'] = p2
        data_dict['To_reading_KVAH'] = values[4]
    data_dict['KGStartReading'] = '0'
    data_dict['KGEndReading'] = '0'
    data_dict['CircleName'] = 'UP West'
    data_dict['DiscomName'] = 'Paschimanchal Vidut vitran Nigam ltd'
    data_dict['MeterRent'] = '0'
    print(data_dict)
 
     # Function to be called for Indus ID as of now its hardcoded
    # print(data_dict.get("Account No").strip())
    # Indus_id = get_indus_id(data_dict.get("Account No").strip())
##    Indus_id = ""
##    data_dict["indusid"] = Indus_id
##    with open(data2, "rb") as img_file:
##        encoded_string = base64.b64encode(img_file.read())
##        encoded_string = encoded_string.decode("utf-8")
##    data_dict["attachment_name"] = file_name
##    data_dict["encoded_string"] = encoded_string
##    # For mapping to api dictionary
##    map_data = api_mapping(data_dict)
##    map_data1 = map_data
##    #print(map_data1)
##    print("++++++++++++++++++++++++++++++++")
##    # For Validating  Dictionary
##    checked_data = get_validation(map_data)
##    # Checking validated data
##    final_call = check_api_call(checked_data)
##    print(final_call)
##    if final_call == 'Trigger':
##        for k, v in map_data.items():
##            if v == 'Keyword Not Found':
##                map_data1[k] = '0'
##            else:
##                pass
##        call_post_api = call_api(map_data1)
##        r = call_post_api
##        print(r)
##        split_data = str(r).split(",")
##        staus_code = split_data[0].replace("(","")
##        api_status_code = staus_code
##        value_to_split =str(r).split('Status')
##        if  "Not Success" in value_to_split[1]:
##            api_message = value_to_split[0][25:-7]
##            Remarks = 'EB PORTAL VALIDATION FAILED'
##            status = 'NOT PROCESSED'
##        else:
##            api_message = "SUCCESS"
##            Remarks = 'VALIDATION PASSED'
##            status = 'PROCESSED'
##    else:
##        status = 'NOT PROCESSED'
##        Remarks = 'OCR VALIDATION FAILED'
##        api_respnse = ''
##    data_dict.pop('encoded_string')
##    call_db_post((map_data1.get("IndusSiteID"), map_data1.get("AccountNumber"), map_data1.get("BillNumber"),
##                  map_data1.get("BillingDate"), map_data1.get("DueDate"),
##                  map_data1.get("DisconnectionDate"), map_data1.get("DISCOMEntryDate"), map_data1.get("PowerFactor"),
##                  map_data1.get("MaximumDemand"), map_data1.get("BillType"),
##                  map_data1.get("MeterComplexity"), map_data1.get("StartDate"), map_data1.get("EndDate"),
##                  map_data1.get("KWHStartReading"), map_data1.get("KWHEndReading"),
##                  map_data1.get("KVAHStartReading"), map_data1.get("KVAHEndReading"), map_data1.get("KGStartReading"),
##                  map_data1.get("KGEndReading"), map_data1.get("BilledUnit"),
##                  map_data1.get("EnergyCharges"), map_data1.get("DemandCharges"), map_data1.get("MeterRent"),
##                  map_data1.get("FixedCharges"), map_data1.get("FuelSurcharge"),
##                  map_data1.get("RegulatoryCharges"), map_data1.get("PPACCharges"), map_data1.get("DevelopmentCharges"),
##                  map_data1.get("MiscellaneousCharges"), map_data1.get("ArrearAmount1"),
##                  map_data1.get("ArrearStartDate1"), map_data1.get("ArrearEndDate1"), map_data1.get("ArrearType1"),
##                  map_data1.get("InstallmentNumber1"), map_data1.get("ArrearRemarks1"),
##                  map_data1.get("ArrearAmount2"), map_data1.get("ArrearStartDate2"), map_data1.get("ArrearEndDate2"),
##                  map_data1.get("ArrearType2"), map_data1.get("InstallmentNumber2"),
##                  map_data1.get("ArrearRemarks2"), map_data1.get("ArrearAmount3"), map_data1.get("ArrearStartDate3"),
##                  map_data1.get("ArrearEndDate3"), map_data1.get("ArrearType3"),
##                  map_data1.get("InstallmentNumber3"), map_data1.get("ArrearRemarks3"),
##                  map_data1.get("CurrentBillLPSC"), map_data1.get("ArrearLPSC"), map_data1.get("PowerFactorPenalty"),
##                  map_data1.get("VCRPenalty"), map_data1.get("MDISanctionLoadPenalty"),
##                  map_data1.get("TheftandManipulations"), map_data1.get("OtherPenalty"),
##                  map_data1.get("PenaltyRemarks"),
##                  map_data1.get("InterestonDeposit"), map_data1.get("TaxonInterestonDeposit"),
##                  map_data1.get("AdditionalSecurityDepositAmount"), map_data1.get("PromptPaymentRebate"),
##                  map_data1.get("SecurityRefund"),
##                  map_data1.get("PenaltyRefund"), map_data1.get("RoundOffRefund"), map_data1.get("OtherRefund"),
##                  map_data1.get("RefundAmountforCustomer"), map_data1.get("CustomerRefundStartDate"),
##                  map_data1.get("CustomerRefundEndDate"), map_data1.get("RefundAmountforIndus"),
##                  map_data1.get("IndusRefundStartDate"), map_data1.get("IndusRefundEndDate"),
##                  map_data1.get("RefundRemarks"),
##                  map_data1.get("TaxesandDuties"), map_data1.get("ElectricitySurcharge"),
##                  map_data1.get("GovernmentDuty"), map_data1.get("IGST"), map_data1.get("CGST"),
##                  map_data1.get("SGST"), map_data1.get("EBAmountBeforeDue"), map_data1.get("EBAmountAfterDue"),
##                  map_data1.get("EBAmountFinal"), map_data1.get("RoundOffAmount"),
##                  map_data1.get("RebateAmount"), map_data1.get("MeterReplacementCharges"),
##                  map_data1.get("SecurityRemarks"), map_data1.get("DifferenceReasonRemarks"),
##                  map_data1.get("EBDifferenceReason"),
##                  map_data1.get("FinalRemarks"), map_data1.get("MeterNumber"), map_data1.get("SanctionLoad"),
##                  map_data1.get("EBSDAmount"), map_data1.get("PPDDate"),
##                  map_data1.get("UserId"), 'UP WEST', 'PVVNL-RURAL', map_data1.get("AttachmentName"), start_t,
##                  datetime.datetime.now(), final_call, r,api_status_code,api_message,str(checked_data),status,Remarks,str(data_dict)))
##
##    return "Success"
##    
  
    
    
if __name__ == "__main__":
    for data in os.listdir(r"C:\Users\Trashi\Desktop\IndusTower\UP West\PVVNL-RURAL\pdfs"):
        data2 = (r'C:\Users\Trashi\Desktop\IndusTower\UP West\PVVNL-RURAL\pdfs\%s') % data
        print(data)
        trigger_tpdl(data2, data)
##        try:
##            print(data)
##            trigger_tpdl(data2, data)
##            path_to_move =  r'E:\OneDrive - Indus Towers Limited\Documents\Project Vidyut\UP WEST\PVVNL RURAL\Processed'
##            shutil.move(data2, path_to_move)
##        except:
##            call_db_post(('', '', '','', '','', '', '','', '','', '','',
##                              '', '', '','', '','', '', '','', '','', '','',
##                              '', '', '','', '','', '', '','', '','', '','',
##                              '', '', '','', '','', '', '','', '','', '','',
##                              '', '', '','', '','', '', '','', '','', '','',
##                              '', '', '','', '','', '', '','', '','', '','',
##                              '', '', '','', '','', '', '','', '','', '','',
##                              'UP WEST', 'PVVNL-RURAL', data, datetime.datetime.now(),
##                  datetime.datetime.now(), '', '', '', '', '', 'FAILED', 'Data Extraction Failed' ,''))
##            path_to_move =  r'E:\OneDrive - Indus Towers Limited\Documents\Project Vidyut\UP WEST\PVVNL RURAL\Not Processed'
##            shutil.move(data2, path_to_move)
####            

