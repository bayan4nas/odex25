
import logging

import requests

from odoo import api, models
from odoo.exceptions import AccessDenied
from odoo.http import request
from suds.client import Client ,SoapClient
import json
from suds.sudsobject import asdict , items

_logger = logging.getLogger(__name__)

class EltezamSOAP(models.Model):
    _name = 'eltezam'
    _description = 'Eltezam SOAP API'
        
    
    def SubmitEmployeeAppraisalInfo(self,EmployeeAppraisalInfoStructure) :
        print(EmployeeAppraisalInfoStructure)
        
    def SubmitEmployeeHistoricalInfo(self,EmployeeHistoricalInfoStructure) :
        print(EmployeeHistoricalInfoStructure)
        
    def SubmitEmployeeInfo(self,EmployeeInfoStructure) :
        print(EmployeeInfoStructure)
        
    def SubmitEmployeePayslipInfo(self,EmployeePayslipInfoStructure) :
        print(EmployeePayslipInfoStructure)
        
    def SubmitEmployeeQualificationInfo(self,EmployeePayslipInfoStructure) :
        print(EmployeePayslipInfoStructure)
        
    def SubmitEmployeeVacationInfo(self,EmployeeVacationInfoStructure) :
        print(EmployeeVacationInfoStructure)
        
    def SubmitJobInfo(self,JobInfoStructure) :
        print(JobInfoStructure)
    
    def recursive_dict(self , data):
        out = {}
        for k, v in items(data):
            if hasattr(v, '__keylist__'):
                out[k] = self.recursive_dict(v)
            elif isinstance(v, list):
                out[k] = []
                for item in v:
                    if hasattr(item, '__keylist__'):
                        out[k].append(self.recursive_dict(item))
                    else:
                        out[k].append(item)
            else:
                out[k] = v
        return out

# Methods (7):
#             SubmitEmployeeAppraisalInfo(ns5:SubmitEmployeeAppraisalInfoRequestStructure employeeAppraisalInfo)
#             SubmitEmployeeHistoricalInfo(ns5:SubmitEmployeeHistoricalInfoRequestStructure employeeHistoricalInfo)
#             SubmitEmployeeInfo(ns5:SubmitEmployeeInfoRequestStructure employeeInfo)
#             SubmitEmployeePayslipInfo(ns5:SubmitEmployeePayslipInfoRequestStructure employeePayslipInfo)
#             SubmitEmployeeQualificationInfo(ns5:SubmitEmployeeQualificationInfoRequestStructure employeeQualificationInfo)
#             SubmitEmployeeVacationInfo(ns5:SubmitEmployeeVacationInfoRequestStructure employeeVacationInfo)
#             SubmitJobInfo(ns5:SubmitJobInfoRequestStructure jobInfo)
#          Types (43):
#             ns2:AcknowledgementStructure
#             ns2:AppraisalInfoStructure
#             ns2:AppraisalTypeCodeType
#             ns2:ArrayOfPayslipStructure
#             ns2:ArrayOfQualificationStructure
#             ns2:ArrayOfVacationStructure
#             ns2:BloodTypeType
#             ns4:CommonErrorStructure
#             ns2:ElementClassificationType
#             ns2:EmployeeInfoStructure
#             ns2:EmployeeJobInfoStructure
#             ns3:GenderType
#             ns2:GradeType
#             ns2:HealthstatusType
#             ns2:JobInfoStructure
#             ns2:MaritalStatusType
#             ns2:PayslipStructure
#             ns3:PersonIdentifierSummaryStructure
#             ns2:PersonNameStructure
#             ns2:PersonalInfoStructure
#             ns2:PositionStatusType
#             ns2:QualificationStatusType
#             ns2:QualificationStructure
#             ns2:ReligionType
#             ns5:SubmitEmployeeAppraisalInfoRequestStructure
#             ns5:SubmitEmployeeHistoricalInfoRequestStructure
#             ns5:SubmitEmployeeInfoRequestStructure
#             ns5:SubmitEmployeePayslipInfoRequestStructure
#             ns5:SubmitEmployeeQualificationInfoRequestStructure
#             ns5:SubmitEmployeeVacationInfoRequestStructure
#             ns5:SubmitJobInfoRequestStructure
#             ns2:TerminationInfoStructure
#             ns2:TransactionTypeType
#             ns2:VacationStructure
#             ns1:YesNoType
#             ns4:errorType
#             ns5:submitEmployeeAppraisalInfoResponseStructure
#             ns5:submitEmployeeHistoricalInfoResponseStructure
#             ns5:submitEmployeeInfoResponseStructure
#             ns5:submitEmployeePayslipInfoResponseStructure
#             ns5:submitEmployeeQualificationInfoResponseStructure
#             ns5:submitEmployeeVacationInfoResponseStructure
#             ns5:submitJobInfoResponseStructure