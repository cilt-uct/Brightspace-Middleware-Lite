# Constants used in this service

## D2L Product Versions ####################
DEFAULT_LP_VERSION  = 1.51
DEFAULT_LE_VERSION  = 1.84
DEFAULT_LR_VERSION  = 1.3
DEFAULT_EP_VERSION  = 2.5
DEFAULT_BFP_VERSION = 1.0
DEFAULT_BAS_VERSION = 1.4

## REGEXP ##################################
RE_COURSE = r'([A-Z]{3}\d{4}[A-Z][E|W|A]{,3})'
RE_COURSE_YEAR = r'([A-Z]{3}\d{4}[A-Z][E|W|A]{,3})[_,]?(\d{4})?'
RE_PROGRAM = r'([A-Z]{2}\d{3})'
RE_PROGRAM_YEAR = r'([A-Z]{2}\d{3})[_,]?(\d{4})?'
RE_COURSE_OR_PROGRAM = r'([A-Z]{3}\d{4}[A-Z][E|W|A]{,3})|([A-Z]{2}\d{3})'
RE_COURSE_OR_PROGRAM_SANS_SUFFIX = r'([A-Z]{3}\d{4})|([A-Z]{2}\d{3})' # AMA-902
RE_COURSE_OR_PROGRAM_YEAR = r'([A-Z]{3}\d{4}[A-Z][E|W|A]{,3})[_,]?(\d{4})?|([A-Z]{2}\d{3})[_,]?(\d{4})?'
RE_VULA_REF_SITE = r'[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}_[0-9]{8}_[0-9]{1,8}'

RE_VALID_CN = r'^(\d{8}|[A-Za-z]{6}\d{3}|T\d{7})$'
RE_STAFF = r'^(\d{8})$'
RE_STUDENT = r'^([A-Za-z]{6}\d{3})$'
RE_THIRDPARTY = r'^(T\d{7})$'
RE_EMAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

COURSE_OFFERING_TYPE = 3

## DEFAULT VALUES #####################################################
OUTYPES = {
    "dept": {
        "Id": 101,
        "Code": "Department",
        "Name": "Department"
    },
    "semester": {
        "Id": 5,
        "Code": "Semester",
        "Name": "Semester"
    },
    "faculty": {
        "Id": 103,
        "Code": "Faculty",
        "Name": "Faculty"
    },
    "template": {
        "Id": 2,
        "Code": "Course Template",
        "Name": "Course Template"
    },
    "program": {
        "Id": 102,
        "Code": "Program",
        "Name": "Program"
    },
    "course": {
        "Id": 3,
        "Code": "Course Offering",
        "Name": "Course Offering"
    },
    "group": {
        "Id": 4,
        "Code": "Group",
        "Name": "Group"
    }
}

# Should be database lookup
ROLES = {
  "Super Administrator": 105,
  "super administrator": 105,
  "Administrator": 116,
  "administrator": 116,
  "Designer": 113,
  "designer": 113,
  "Lecturer": 109,
  "lecturer": 109,
  "Owner": 122,
  "owner": 122,
  "Support Staff": 118,
  "support staff": 118,
  "SupportStaff": 118,
  "supportstaff": 118,
  "LecturerTutor": 126,
  "lecturertutor": 126,
  "Tutor": 114,
  "tutor": 114,
  "Student": 110,
  "student": 110,
  "Guest": 120,
  "guest": 120,
  "Member": 121,
  "member": 121,
  "Observer": 111,
  "observer": 111,
  "Staff": 119,
  "staff": 119,
  "ThirdParty": 128,
  "thirdparty": 128
}

# AMA-733 - Amathuba Announcements Site: Auto enrollments to an org unit
TEACHING_ROLES = [116, 109, 126]

SAKAI_ROLES = {
    "guest": 120,
    "student": 110,
    "staff": 119,
    "thirdparty": 128,
    "lecturer": 109,
    "member": 121,
    "owner": 122
}

OTHER_TERM_TEMPLATE = {
    'other'     : 'UCT_other_template',  # University - wide Community or Activity
    'COM-other' : 'COM_other_template',  # Faculty of Commerce
    'COM'       : 'COM_other_template',
    'EBE-other' : 'EBE_other_template',  # Faculty of Engineering & Built Environment
    'EBE'       : 'EBE_other_template',
    'FHS-other' : 'FHS_other_template',  # Faculty of Health Sciences
    'FHS'       : 'FHS_other_template',
    'HUM-other' : 'HUM_other_template',  # Faculty of Humanities
    'HUM'       : 'HUM_other_template',
    'LAW-other' : 'LAW_other_template',  # Faculty of Law
    'LAW'       : 'LAW_other_template',
    'SCI-other' : 'SCI_other_template',  # Faculty of Science
    'SCI'       : 'SCI_other_template',
    'GSB-other' : 'GSB_other_template',  # Graduate School of Business (GSB)
    'GSB'       : 'GSB_other_template',
    'CHED-other': 'CHED_other_template',  # Centre for Higher Education Development
    'CHED'      : 'CHED_other_template'
}
