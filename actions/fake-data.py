#!/usr/bin/env python

from collections import defaultdict
from faker import Faker
import logging
import random

_logger = logging.getLogger(__name__)

CREATE_MULTI = True  # True for odoo >= saas-11.5
NUMBER_COMPANIES = 2
NUMBER_USERS = 50
NUMBER_PARTNERS = 200
NUMBER_PROJECTS = 10
NUMBER_STAGES = 5
NUMBER_TASKS = 1000
NUMBER_ATTACHMENTS = 200
NUMBER_MESSAGES = 5000
LOCALE = 'fr_FR'

fake = Faker(LOCALE)


class Record:

    model_name = 'unknown'
    default_count = 0

    def __init__(self, odoo_envrionment, reuse_records=None):
        if self.model_name not in odoo_envrionment:
            raise ValueError(f"Model {self.model_name} not found in odoo environment")
        self.env = odoo_envrionment
        self.model = odoo_envrionment[self.model_name]
        self.previous = defaultdict(list)
        if reuse_records:
            for record in reuse_records:
                print(record)
                self.previous[record._name].append(record)

    def generate_data(self, count=0):
        if not count:
            count = self.default_count
        _logger.info(f"Generate {count} records of type '{self.model_name}'")
        if CREATE_MULTI:
            records = []
            for _ in range(count):
                records.append(self.prepare_create_data())
            records = list(self.model.create(records))
        else:
            records = []
            for _ in range(count):
                create_data = self.prepare_create_data()
                records.append(self.model.create(create_data))
        return records

    def prepare_create_data(self):
        raise NotImplementedError()

class ResCompany(Record):

    model_name = 'res.company'
    default_count = 2

    def prepare_create_data(self):
        return {
            'name': fake.company() + " " + fake.company_suffix(),
        }

class ResUsers(Record):

    model_name = 'res.users'
    default_count = 50

    def prepare_create_data(self):
        if 'res.company' in self.previous:
            company_id = random.choice(self.previous['res.company']).id
        else:
            company_id = random.choice(self.env['res.company'].search([]).ids)
        email = fake.safe_email()
        return {
            'login': email,
            'email': email,
            'name': fake.name(),
            'password': fake.password,
            'company_id': company_id,
            'company_ids': [(6, 0, [company_id])],
        }

class ResPartner(Record):

    model_name = 'res.partner'
    default_count = 200

    def prepare_create_data(self):
        return {
            'email': fake.safe_email(),
            'name': fake.name(),
            'customer': bool(int(random.random()*2)),
            'supplier': bool(int(random.random()*2)),
            'website': bool(int(random.random()*1.2)) and fake.url(),
            'company_id': False,
        }

generate_models = [ResUsers, ResPartner]
# records = []
# for model in generate_models:
#     instance = model(self.env, records)
#     records.extend(instance.generate_data())

# self.env.cr.commit()
# print(f"generate {NUMBER_COMPANIES} companies")
# companies = []
# for _ in range(NUMBER_COMPANIES):
#     companies.append({
#         'name': fake.company() + " " + fake.company_suffix(),
#     })
# companies = self.env['res.company'].create(companies)
companies = self.env['res.company'].browse(1)

# print(f"generate {NUMBER_USERS} users")
# users = []
# for _ in range(NUMBER_USERS):
#     email = fake.safe_email()
#     company = random.choice(companies).id
#     users.append({
#         'login': email,
#         'email': email,
#         'name': fake.name(),
#         'password': fake.password,
#         'company_id': company,
#         'company_ids': [(6, 0, [company])],
#     })
# users = self.env['res.users'].create(users)
users = self.env['res.users'].search([('login', 'in', ['admin', 'demo'])])

# print(f"generate {NUMBER_PARTNERS} partners")
# partners = []
# for _ in range(NUMBER_PARTNERS):
#     partners.append({
#         'email': fake.safe_email(),
#         'name': fake.name(),
#         'customer': bool(int(random.random()*2)),
#         'supplier': bool(int(random.random()*2)),
#         'website': bool(int(random.random()*1.2)) and fake.url(),
#         'company_id': False,
#     })
# partners = self.env['res.partner'].create(partners)
# self.env.cr.commit()

# print(f"generate {NUMBER_PROJECTS} projects")
# projects = []
# for _ in range(NUMBER_PROJECTS):
#     projects.append({
#         'name': fake.sentence(nb_words=3),
#         'sequence': int(random.random() * 100),
#         'label_tasks': fake.word(),
#         'color': int(random.random() * 256),
#         'company_id': random.choice(companies).id
#     })
# projects = self.env['project.project'].create(projects)

# print(f"generate {NUMBER_STAGES} stages")
# stages = []
# for _ in range(NUMBER_STAGES):
#     stages.append({
#         'name': fake.word(),
#         'sequence': int(random.random() * 100),
#         'project_ids': [(6, 0, [p.id for p in projects])],
#     })
# stages = self.env['project.task.type'].create(stages)

# print(f"generate {NUMBER_TASKS} tasks")
# tasks = []
# for _ in range(NUMBER_TASKS):
#     tasks.append({
#         'name': fake.sentence(nb_words=4),
#         'sequence': int(random.random() * 100),
#         'description': fake.text(max_nb_chars=500),
#         'project_id': random.choice(projects).id,
#         'partner_id': bool(int(random.random()*1.5)) and random.choice(partners).id,
#         'color': int(random.random() * 256),
#         'stage_id': random.choice(stages).id,
#         'user_id': random.choice(users).id,
#     })
# tasks = self.env['project.task'].create(tasks)
# self.env.cr.commit()

# print(f"generate {NUMBER_ATTACHMENTS} attachments")
# attachments = []
# for _ in range(NUMBER_ATTACHMENTS):
#     filename = fake.file_name()
#     attachments.append({
#         'name': filename,
#         'datas_fname': filename,
#         'res_model': 'project.task',
#         'res_id': random.choice(tasks).id
#     })
# attachments = self.env['ir.attachment'].create(attachments)
tasks = self.env['sale.order'].search([])
print(f"post {NUMBER_MESSAGES} messages")
messages = []
for _ in range(NUMBER_MESSAGES):
    user = random.choice(users)
    filename = fake.file_name()
    attachments = bool(int(random.random()*1.5)) and \
        self.env['ir.attachment'].create({
            'name': filename,
            'datas_fname': filename,
        }).ids or []
    random.choice(tasks).sudo(user=user.id).message_post(body=fake.sentence(nb_words=10), attachment_ids=attachments)

self.env.cr.commit()
