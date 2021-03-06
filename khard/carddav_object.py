#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, string, random, datetime
import vobject

class CarddavObject:
    def __init__(self, addressbook_name, addressbook_path, filename=""):
        self.addressbook_name = addressbook_name
        self.addressbook_path = addressbook_path
        if filename == "":
            # create new vcard
            self.vcard = vobject.vCard()
            choice = string.ascii_uppercase + string.digits
            uid_obj = self.vcard.add('uid')
            uid_obj.value = ''.join([random.choice(choice) for _ in range(36)])
        else:
            # create vcard from file
            file = open(filename, "r")
            self.vcard = vobject.readOne(file.read())
            file.close()

    def __str__(self):
        return self.get_full_name()

    def process_user_input(self, input):
        # parse user input string
        contact_data = {}
        counter = 1
        for line in input.splitlines():
            if line == "" or line.startswith("#"):
                continue
            try:
                key = line.split("=")[0].strip().lower()
                value = line.split("=")[1].strip()
                if value == "":
                    continue
                if contact_data.has_key(key):
                    print "Error in input line %d: key %s already exists" % (counter, key)
                    sys.exit(1)
                contact_data[key] = value.decode("utf-8")
                counter += 1
            except IndexError as e:
                print "Error in input line %d: Malformed input\nLine: %s" % (counter, line)
                sys.exit(1)

        # clean vcard
        self.clean_vcard()
        # process data
        # update ref
        dt = datetime.datetime.now()
        rev_obj = self.vcard.add('rev')
        rev_obj.value = "%.4d%.2d%.2dT%.2d%.2d%.2dZ" \
                % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second) 

        # name and organisation
        # either enter first and last name or organisation
        if (contact_data.has_key("first name") and contact_data['first name'] != "" \
                and contact_data.has_key("last name") and contact_data['last name'] != "") \
                or (contact_data.has_key("organisation") and contact_data['organisation'] != ""):
            if contact_data.has_key("first name") == False:
                contact_data['first name'] = ""
            if contact_data.has_key("last name") == False:
                contact_data['last name'] = ""
            if contact_data.has_key("organisation") == False:
                contact_data['organisation'] = ""
            self.set_name_and_organisation(contact_data['first name'],
                    contact_data['last name'], contact_data['organisation'])
        else:
            print "You must at least enter a first and last name or an organisation"
            sys.exit(1)

        # phone
        phone_list = []
        for key in contact_data.keys():
            if key.startswith("phone") == False:
                continue
            try:
                label = contact_data[key].split(":")[0].strip()
                number = contact_data[key].split(":")[1].strip()
                if label == "" or number == "":
                    print "Missing label or number for line %s" % key
                    sys.exit(1)
            except IndexError as e:
                print "The %s line is malformed" % key
                sys.exit(1)
            phone_list.append({"type":label, "value":number})
        if phone_list.__len__() > 0:
            self.set_phone_numbers(phone_list)

        # email
        email_list = []
        for key in contact_data.keys():
            if key.startswith("email") == False:
                continue
            try:
                label = contact_data[key].split(":")[0].strip()
                email = contact_data[key].split(":")[1].strip()
                if label == "" or email == "":
                    print "Missing label or number for line %s" % key
                    sys.exit(1)
            except IndexError as e:
                print "The %s line is malformed" % key
                sys.exit(1)
            email_list.append({"type":label, "value":email})
        if email_list.__len__() > 0:
            self.set_email_addresses(email_list)

        # post addresses
        address_list = []
        for key in contact_data.keys():
            if key.startswith("address") == False:
                continue
            try:
                label = contact_data[key].split(":")[0].strip()
                address = contact_data[key].split(":")[1].strip()
                if label == "" or address == "":
                    print "Warning: Missing label or value for line %s" % key
                    continue
            except IndexError as e:
                print "Warning: The %s line is malformed" % key
                continue
            if address.split(";").__len__() != 5:
                print "Warning: The %s line is malformed" % key
                continue
            street_and_house_number = address.split(";")[0].strip()
            if street_and_house_number == "":
                print "Warning: %s has no street" % key
                continue
            postcode = address.split(";")[1].strip()
            if postcode == "":
                print "Warning: %s has no postcode" % key
                continue
            city = address.split(";")[2].strip()
            if city == "":
                print "Warning: %s has no city" % key
                continue
            region = address.split(";")[3].strip()
            country = address.split(";")[4].strip()
            if country == "":
                print "Warning: %s has no country" % key
                continue
            address_list.append({"type":label, "street_and_house_number":street_and_house_number,
                    "postcode":postcode, "city":city, "region":region, "country":country})
        if address_list.__len__() > 0:
            self.set_post_addresses(address_list)

        # birthday
        if contact_data.has_key("birthday") and contact_data['birthday'] != "":
            try:
                date = datetime.datetime.strptime(contact_data['birthday'], "%d.%m.%Y")
                self.set_birthday(date)
            except ValueError as e:
                print "Birthday date in the wrong format. Example: 31.12.1989"
                sys.exit(1)

    def get_addressbook_name(self):
        return self.addressbook_name

    def get_first_name(self):
        return self.vcard.n.value.given.encode("utf-8")

    def get_last_name(self):
        return self.vcard.n.value.family.encode("utf-8")

    def get_full_name(self):
        return self.vcard.fn.value.encode("utf-8")

    def get_organisation(self):
        try:
            return ' '.join(self.vcard.org.value).encode("utf-8")
        except AttributeError as e:
            return ""

    def set_name_and_organisation(self, first_name, last_name, organisation):
        if first_name == "" or last_name == "":
            name_obj = self.vcard.add('fn')
            name_obj.value = organisation
            name_obj = self.vcard.add('n')
            name_obj.value = vobject.vcard.Name(family="", given="")
            showas_obj = self.vcard.add('x-abshowas')
            showas_obj.value = "COMPANY"
        else:
            name_obj = self.vcard.add('fn')
            name_obj.value = "%s %s" % (first_name, last_name)
            name_obj = self.vcard.add('n')
            name_obj.value = vobject.vcard.Name(family=last_name, given=first_name)
        if organisation != "":
            org_obj = self.vcard.add('org')
            org_obj.value = [organisation]

    def get_phone_numbers(self):
        phone_list = []
        for child in self.vcard.getChildren():
            if child.name != "TEL":
                continue
            type = "voice"
            if child.params.has_key("TYPE"):
                type = ','.join(child.params['TYPE']).encode("utf-8")
            elif child.group != None:
                for label in self.vcard.getChildren():
                    if label.name == "X-ABLABEL" and label.group == child.group:
                        type = label.value.encode("utf-8")
                        break
            phone_list.append({"type":type, "value":child.value.encode("utf-8")})
        return phone_list

    def set_phone_numbers(self, phone_list):
        for index, entry in enumerate(phone_list):
            phone_obj = self.vcard.add('tel')
            phone_obj.value = entry['value']
            if entry['type'].lower() in ["cell", "home", "work",]:
                phone_obj.type_param = entry['type']
            else:
                group_name = "itemtel%d" % (index+1)
                phone_obj.group = group_name
                label_obj = self.vcard.add('x-ablabel')
                label_obj.group = group_name
                label_obj.value = entry['type']

    def get_email_addresses(self):
        email_list = []
        for child in self.vcard.getChildren():
            if child.name != "EMAIL":
                continue
            type = "home"
            if child.params.has_key("TYPE"):
                type = ','.join(child.params['TYPE']).encode("utf-8")
            elif child.group != None:
                for label in self.vcard.getChildren():
                    if label.name == "X-ABLABEL" and label.group == child.group:
                        type = label.value.encode("utf-8")
                        break
            email_list.append({"type":type, "value":child.value.encode("utf-8")})
        return email_list

    def set_email_addresses(self, email_list):
        for index, entry in enumerate(email_list):
            email_obj = self.vcard.add('email')
            email_obj.value = entry['value']
            if entry['type'].lower() in ["home", "work",]:
                email_obj.type_param = entry['type']
            else:
                group_name = "itememail%d" % (index+1)
                email_obj.group = group_name
                label_obj = self.vcard.add('x-ablabel')
                label_obj.group = group_name
                label_obj.value = entry['type']

    def get_post_addresses(self):
        address_list = []
        for child in self.vcard.getChildren():
            if child.name != "ADR":
                continue
            type = "home"
            if child.params.has_key("TYPE"):
                type = ','.join(child.params['TYPE']).encode("utf-8")
            elif child.group != None:
                for label in self.vcard.getChildren():
                    if label.name == "X-ABLABEL" and label.group == child.group:
                        type = label.value.encode("utf-8")
                        break
            address_list.append({"type":type,
                    "street_and_house_number":child.value.street.encode("utf-8"),
                    "postcode":child.value.code.encode("utf-8"),
                    "city":child.value.city.encode("utf-8"),
                    "region":child.value.region.encode("utf-8"),
                    "country":child.value.country.encode("utf-8")})
        return address_list

    def set_post_addresses(self, address_list):
        for index, entry in enumerate(address_list):
            adr_obj = self.vcard.add('adr')
            adr_obj.value = vobject.vcard.Address(street=entry['street_and_house_number'],
                    city=entry['city'], region=entry['region'],
                    code=entry['postcode'], country=entry['country'])
            if entry['type'].lower() in ["home", "work",]:
                adr_obj.type_param = entry['type']
            else:
                group_name = "itemadr%d" % (index+1)
                adr_obj.group = group_name
                label_obj = self.vcard.add('x-ablabel')
                label_obj.group = group_name
                label_obj.value = entry['type']

    def get_birthday(self):
        """:returns: contacts birthday or None if not available
            :rtype: datetime.datetime
        """
        try:
            return datetime.datetime.strptime(self.vcard.bday.value, "%Y%m%d")
        except AttributeError as e:
            return None
        except ValueError as e:
            return None

    def set_birthday(self, date):
        bday_obj = self.vcard.add('bday')
        bday_obj.value = "%.4d%.2d%.2d" % (date.year, date.month, date.day)

    def print_vcard(self):
        strings = ["Name: %s" % self.get_full_name()]
        if self.get_phone_numbers().__len__() > 0:
            strings.append("Phone")
            for index, entry in enumerate(self.get_phone_numbers()):
                strings.append("    %s: %s" % (entry['type'], entry['value']))
        if self.get_email_addresses().__len__() > 0:
            strings.append("E-Mail")
            for index, entry in enumerate(self.get_email_addresses()):
                strings.append("    %s: %s" % (entry['type'], entry['value']))
        if self.get_post_addresses().__len__() > 0:
            strings.append("Addresses")
            for index, entry in enumerate(self.get_post_addresses()):
                strings.append("    %s:" % entry['type'])
                strings.append("        %s" % entry['street_and_house_number'])
                strings.append("        %s, %s" % (entry['postcode'], entry['city']))
                if entry['region'] != "":
                    strings.append("        %s, %s" % (entry['region'], entry['country']))
                else:
                    strings.append("        %s" % entry['country'])
        if self.get_birthday() != None:
            strings.append("Miscellaneous")
            date = self.get_birthday()
            strings.append("    Birthday: %.2d.%.2d.%.4d" % (date.day, date.month, date.year))
        return '\n'.join(strings)

    def write_to_file(self, overwrite=False):
        print self.vcard.serialize()
        vcard_filename = os.path.join( self.addressbook_path,
                self.vcard.uid.value + ".vcf")
        if os.path.exists(vcard_filename) and overwrite == False:
            print "Error: vcard with the file name %s already exists" % os.path.basename(vcard_filename)
            sys.exit(4)
        try:
            vcard_output = self.vcard.serialize()
            file = open(vcard_filename, "w")
            file.write(vcard_output)
            file.close()
        except vobject.base.ValidateError as e:
            print "Error: Vcard is not valid.\n%s" % e
            sys.exit(4)

    def clean_vcard(self):
        # rev
        try:
            self.vcard.remove(self.vcard.rev)
        except AttributeError as e:
            pass
        # name
        try:
            self.vcard.remove(self.vcard.n)
            self.vcard.remove(self.vcard.fn)
        except AttributeError as e:
            pass
        # organisation
        try:
            self.vcard.remove(self.vcard.org)
        except AttributeError as e:
            pass
        try:
            self.vcard.remove(self.vcard.x_abshowas)
        except AttributeError as e:
            pass
        # phone
        while True:
            try:
                self.vcard.remove(self.vcard.tel)
            except AttributeError as e:
                break
        # email addresses
        while True:
            try:
                self.vcard.remove(self.vcard.email)
            except AttributeError as e:
                break
        # addresses
        while True:
            try:
                self.vcard.remove(self.vcard.adr)
            except AttributeError as e:
                break
        # birthday
        try:
            self.vcard.remove(self.vcard.bday)
        except AttributeError as e:
            pass
        # x-ablabel
        while True:
            try:
                self.vcard.remove(self.vcard.x_ablabel)
            except AttributeError as e:
                break

    def delete_vcard_file(self):
        vcard_filename = os.path.join( self.addressbook_path,
                self.vcard.uid.value + ".vcf")
        if os.path.exists(vcard_filename):
            os.remove(vcard_filename)

