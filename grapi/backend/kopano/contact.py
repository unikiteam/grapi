# SPDX-License-Identifier: AGPL-3.0-or-later
import logging
from datetime import datetime
from .item import ItemResource, get_email2
from .resource import _date
from .utils import HTTPBadRequest, _folder, _item, _server_store, _set_value_by_tag, _set_value_per_tag, experimental

from MAPI.Tags import (
    PR_ATTACHMENT_CONTACTPHOTO, PR_GIVEN_NAME_W, PR_MIDDLE_NAME_W,
    PR_SURNAME_W, PR_NICKNAME_W, PR_TITLE_W, PR_GENERATION_W, PR_BODY_W,
    PR_COMPANY_NAME_W, PR_MOBILE_TELEPHONE_NUMBER_W, PR_CHILDRENS_NAMES_W,
    PR_BIRTHDAY, PR_SPOUSE_NAME_W, PR_INITIALS_W, PR_DISPLAY_NAME_PREFIX_W,
    PR_DEPARTMENT_NAME_W, PR_OFFICE_LOCATION_W, PR_PROFESSION_W,
    PR_MANAGER_NAME_W, PR_ASSISTANT_W, PR_BUSINESS_HOME_PAGE_W,
    PR_HOME_TELEPHONE_NUMBER_W, PR_HOME2_TELEPHONE_NUMBER_W,
    PR_BUSINESS_TELEPHONE_NUMBER_W, PR_BUSINESS2_TELEPHONE_NUMBER_W,
    PR_HOME_ADDRESS_STREET_W, PR_HOME_ADDRESS_CITY_W,
    PR_HOME_ADDRESS_POSTAL_CODE_W, PR_HOME_ADDRESS_STATE_OR_PROVINCE_W,
    PR_HOME_ADDRESS_COUNTRY_W, PR_OTHER_ADDRESS_STREET_W,
    PR_OTHER_ADDRESS_CITY_W, PR_OTHER_ADDRESS_POSTAL_CODE_W,
    PR_OTHER_ADDRESS_STATE_OR_PROVINCE_W, PR_OTHER_ADDRESS_COUNTRY_W,
)

# TODO import constants
PidLidYomiFirstName = 'PT_UNICODE:PSETID_Address:0x802C'
PidLidYomiLastName = 'PT_UNICODE:PSETID_Address:0x802D'
PidLidYomiCompanyName = 'PT_UNICODE:PSETID_Address:0x802E'
PidLidFileUnder = 'PT_UNICODE:PSETID_Address:0x8005'
PidLidInstantMessagingAddress = 'PT_UNICODE:PSETID_Address:0x8062'
PidLidWorkAddressStreet = 'PT_UNICODE:PSETID_Address:0x8045'
PidLidWorkAddressCity = 'PT_UNICODE:PSETID_Address:0x8046'
PidLidWorkAddressState = 'PT_UNICODE:PSETID_Address:0x8047'
PidLidWorkAddressPostalCode = 'PT_UNICODE:PSETID_Address:0x8048'
PidLidWorkAddressCountry = 'PT_UNICODE:PSETID_Address:0x8049'


def set_email_addresses(item, arg):  # TODO multiple via pyko
    item.address1 = '%s <%s>' % (arg[0]['name'], arg[0]['address'])


def _phys_address(addr):
    data = {
        'street': addr.street,
        'city': addr.city,
        'postalCode': addr.postal_code,
        'state': addr.state,
        'countryOrRegion': addr.country
    }
    return {a: b for (a, b) in data.items() if b}


PHYS_ADDRESS_HOME = 'home'
PHYS_ADDRESS_BUSINESS = 'business'
PHYS_ADDRESS_OTHER = 'other'
PHYS_ADDRESS_DICT = {
    PHYS_ADDRESS_HOME: {
        'street': PR_HOME_ADDRESS_STREET_W,
        'city': PR_HOME_ADDRESS_CITY_W,
        'postalCode': PR_HOME_ADDRESS_POSTAL_CODE_W,
        'state': PR_HOME_ADDRESS_STATE_OR_PROVINCE_W,
        'countryOrRegion': PR_HOME_ADDRESS_COUNTRY_W,
    },
    PHYS_ADDRESS_BUSINESS: {
        'street': PidLidWorkAddressStreet,
        'city': PidLidWorkAddressCity,
        'postalCode': PidLidWorkAddressPostalCode,
        'state': PidLidWorkAddressState,
        'countryOrRegion': PidLidWorkAddressCountry,
    },
    PHYS_ADDRESS_OTHER: {
        'street': PR_OTHER_ADDRESS_STREET_W,
        'city': PR_OTHER_ADDRESS_CITY_W,
        'postalCode': PR_OTHER_ADDRESS_POSTAL_CODE_W,
        'state': PR_OTHER_ADDRESS_STATE_OR_PROVINCE_W,
        'countryOrRegion': PR_OTHER_ADDRESS_COUNTRY_W,
    },
}


def _set_phys_address(item, args: dict, prop_tags: dict):
    try:
        is_args_list = True
        is_proptags_list = True
        if not isinstance(args, dict):
            logging.error("args is not a dict")
            is_args_list = False
        if not isinstance(prop_tags, dict):
            logging.error("proptags is not a dict")
            is_proptags_list = False
        if not is_args_list or not is_proptags_list:
            return
    except NameError:
        logging.exception('Parameter(s) not defined')
    for name, arg in args.items():
        if name in prop_tags:
            _set_value_by_tag(item, arg, prop_tags[name])


def _set_birthday(item, arg: str):
    if arg.endswith("Z"):
        arg = arg.replace("Z", "+0000")
    # TODO must end with + and 4 0's
    bday = datetime.strptime(arg, '%Y-%m-%dT%H:%M:%S.%f%z')
    _set_value_by_tag(item, bday, PR_BIRTHDAY)


class DeletedContactResource(ItemResource):
    fields = {
        '@odata.type': lambda item: '#microsoft.graph.contact',  # TODO
        'id': lambda item: item.entryid,
        '@removed': lambda item: {'reason': 'deleted'}  # TODO soft deletes
    }


@experimental
class ContactResource(ItemResource):
    fields = ItemResource.fields.copy()
    fields.update({
        'displayName': lambda item: item.name,
        'emailAddresses': lambda item: [get_email2(a) for a in item.addresses()],
        'parentFolderId': lambda item: item.folder.entryid,
        'givenName': lambda item: item.first_name or None,
        'middleName': lambda item: item.middle_name or None,
        'surname': lambda item: item.last_name or None,
        'nickName': lambda item: item.nickname or None,
        'title': lambda item: item.title or None,
        'companyName': lambda item: item.company_name or None,
        'mobilePhone': lambda item: item.mobile_phone or None,
        'personalNotes': lambda item: item.text,
        'generation': lambda item: item.generation or None,
        'children': lambda item: item.children,
        'spouseName': lambda item: item.spouse or None,
        'birthday': lambda item: item.birthday and _date(item.birthday) or None,
        'initials': lambda item: item.initials or None,
        'yomiGivenName': lambda item: item.yomi_first_name or None,
        'yomiSurname': lambda item: item.yomi_last_name or None,
        'yomiCompanyName': lambda item: item.yomi_company_name or None,
        'fileAs': lambda item: item.file_as,
        'jobTitle': lambda item: item.job_title or None,
        'department': lambda item: item.department or None,
        'officeLocation': lambda item: item.office_location or None,
        'profession': lambda item: item.profession or None,
        'manager': lambda item: item.manager or None,
        'assistantName': lambda item: item.assistant or None,
        'businessHomePage': lambda item: item.business_homepage or None,
        'homePhones': lambda item: item.home_phones,
        'businessPhones': lambda item: item.business_phones,
        'imAddresses': lambda item: item.im_addresses,
        'homeAddress': lambda item: _phys_address(item.home_address),
        'businessAddress': lambda item: _phys_address(item.business_address),
        'otherAddress': lambda item: _phys_address(item.other_address),
    })

    set_fields = {
        'displayName': lambda item, arg: setattr(item, 'name', arg),
        'emailAddresses': set_email_addresses,
        'givenName': lambda item, arg: _set_value_by_tag(item, arg, PR_GIVEN_NAME_W),
        'middleName': lambda item, arg: _set_value_by_tag(item, arg, PR_MIDDLE_NAME_W),
        'surname': lambda item, arg: _set_value_by_tag(item, arg, PR_SURNAME_W),
        'nickName': lambda item, arg: _set_value_by_tag(item, arg, PR_NICKNAME_W),
        'title': lambda item, arg: _set_value_by_tag(item, arg, PR_DISPLAY_NAME_PREFIX_W),
        'companyName': lambda item, arg: _set_value_by_tag(item, arg, PR_COMPANY_NAME_W),
        'mobilePhone': lambda item, arg: _set_value_by_tag(item, arg, PR_MOBILE_TELEPHONE_NUMBER_W),
        'personalNotes': lambda item, arg: _set_value_by_tag(item, str(arg), PR_BODY_W),
        'generation': lambda item, arg: _set_value_by_tag(item, arg, PR_GENERATION_W),
        'children': lambda item, arg: _set_value_by_tag(item, arg, PR_CHILDRENS_NAMES_W),
        'spouseName': lambda item, arg: _set_value_by_tag(item, arg, PR_SPOUSE_NAME_W),
        'birthday': lambda item, arg: _set_birthday(item, arg),
        'initials': lambda item, arg: _set_value_by_tag(item, arg, PR_INITIALS_W),
        'yomiGivenName': lambda item, arg: _set_value_by_tag(item, arg, PidLidYomiFirstName),
        'yomiSurname': lambda item, arg: _set_value_by_tag(item, arg, PidLidYomiLastName),
        'yomiCompanyName': lambda item, arg: _set_value_by_tag(item, arg, PidLidYomiCompanyName),
        'fileAs': lambda item, arg: _set_value_by_tag(item, arg, PidLidFileUnder),
        'jobTitle': lambda item, arg: _set_value_by_tag(item, arg, PR_TITLE_W),
        'department': lambda item, arg: _set_value_by_tag(item, arg, PR_DEPARTMENT_NAME_W),
        'officeLocation': lambda item, arg: _set_value_by_tag(item, arg, PR_OFFICE_LOCATION_W),
        'profession': lambda item, arg: _set_value_by_tag(item, arg, PR_PROFESSION_W),
        'manager': lambda item, arg: _set_value_by_tag(item, arg, PR_MANAGER_NAME_W),
        'assistantName': lambda item, arg: _set_value_by_tag(item, arg, PR_ASSISTANT_W),
        'businessHomePage': lambda item, arg: _set_value_by_tag(item, arg, PR_BUSINESS_HOME_PAGE_W),
        'homePhones': lambda item, arg: _set_value_per_tag(item, arg, [PR_HOME_TELEPHONE_NUMBER_W,
                                                                       PR_HOME2_TELEPHONE_NUMBER_W]),
        'businessPhones': lambda item, arg: _set_value_per_tag(item, arg, [PR_BUSINESS_TELEPHONE_NUMBER_W,
                                                                           PR_BUSINESS2_TELEPHONE_NUMBER_W]),
        'imAddresses': lambda item, arg: _set_value_by_tag(item, ', '.join(arg), PidLidInstantMessagingAddress),
        'homeAddress': lambda item, arg: _set_phys_address(item, arg, PHYS_ADDRESS_DICT[PHYS_ADDRESS_HOME]),
        'businessAddress': lambda item, arg: _set_phys_address(item, arg, PHYS_ADDRESS_DICT[PHYS_ADDRESS_BUSINESS]),
        'otherAddress': lambda item, arg: _set_phys_address(item, arg, PHYS_ADDRESS_DICT[PHYS_ADDRESS_OTHER]),
    }

    deleted_resource = DeletedContactResource

    def handle_get(self, req, resp, store, server, folderid, itemid):
        folder = _folder(store, folderid or 'contacts')  # TODO all folders?

        if itemid:
            if itemid == 'delta':
                self._handle_get_delta(req, resp, folder=folder)
            else:
                self._handle_get_with_itemid(req, resp, folder=folder, itemid=itemid)
        else:
            raise HTTPBadRequest("Missing contact itemid")

    def _handle_get_delta(self, req, resp, folder):
        req.context.deltaid = '{itemid}'
        self.delta(req, resp, folder)

    def _handle_get_with_itemid(self, req, resp, folder, itemid):
        data = _item(folder, itemid)
        self.respond(req, resp, data)

    def on_get(self, req, resp, userid=None, folderid=None, itemid=None, method=None):
        handler = None

        if not method:
            handler = self.handle_get
        else:
            raise HTTPBadRequest("Unsupported contact segment '%s'" % method)

        server, store, userid = _server_store(req, userid, self.options)
        handler(req, resp, store=store, server=server, folderid=folderid, itemid=itemid)

    def handle_delete(self, req, resp, store, server, folderid, itemid):
        item = _item(store, itemid)

        store.delete(item)

        self.respond_204(resp)

    def on_delete(self, req, resp, userid=None, folderid=None, itemid=None):
        handler = self.handle_delete

        server, store, userid = _server_store(req, userid, self.options)
        handler(req, resp, store=store, server=server, folderid=folderid, itemid=itemid)
