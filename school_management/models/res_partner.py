# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 be-cloud.be
#                       Jerome Sonnet <jerome.sonnet@be-cloud.be>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
import threading

import openerp
from openerp import tools, api, fields, models, _
from openerp.exceptions import UserError
from openerp.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

class Partner(models.Model):
    '''Partner'''
    _inherit = 'res.partner'
    
    student = fields.Boolean("Student",default=False)
    teacher = fields.Boolean("Teacher",default=False)
    employee = fields.Boolean("Employee",default=False)
    
    initials = fields.Char('Initials')
    birthplace = fields.Char('Birthplace')
    phone2 = fields.Char('Phone2')
    title = fields.Selection([('Mr', 'Monsieur'),('Mme', 'Madame'),('Mlle', 'Mademoiselle')])
    marial_status = fields.Selection([('M', 'Maried'),('S', 'Single')])
    registration_date = fields.Date('Registration Date')
    email_personnel = fields.Char('Email personnel')
    reg_number = fields.Char('Registration Number')
    mat_number = fields.Char('Matricule Number')
    
    student_current_bloc_id = fields.Many2one('school.individual_bloc', compute='_get_student_current_bloc_id', string='Bloc', store=True)
    student_current_bloc_name = fields.Char(related='student_current_bloc_id.source_bloc_name', string='Current Bloc', store=True)
    student_bloc_ids = fields.One2many('school.individual_bloc', 'student_id', string='Programs')
    is_student_registered = fields.Boolean(compute='_is_student_registered', search="_search_student_registered", store=True)
    
    student_current_course_ids = fields.One2many('school.individual_course', compute='_get_student_current_individual_course_ids', string='Courses')
    student_course_ids = fields.One2many('school.individual_course', 'student_id', string='Courses', domain="[('year_id', '=', self.env.user.current_year_id.id)]")
    
    teacher_current_course_ids = fields.One2many('school.individual_course_proxy', compute='_get_teacher_current_individual_course_ids', string="Current Courses")
    teacher_course_ids = fields.One2many('school.individual_course', 'teacher_id', string='Courses', domain="[('year_id', '=', self.env.user.current_year_id.id)]")
    
    teacher_curriculum_vitae = fields.Html('Curriculum Vitae')
    
    @api.one
    def _get_teacher_current_individual_course_ids(self):
        self.teacher_current_course_ids = self.env['school.individual_course_proxy'].search([['year_id', '=', self.env.user.current_year_id.id], ['teacher_id', '=', self.id]])

    @api.one
    def _get_student_current_individual_course_ids(self):
        self.teacher_current_course_ids = self.env['school.individual_course_proxy'].search([['year_id', '=', self.env.user.current_year_id.id], ['student_id', '=', self.id]])

    @api.one
    @api.depends('student_bloc_ids')
    def _get_student_current_bloc_id(self):
        for bloc in self.student_bloc_ids:
            if bloc.year_id == self.env.user.current_year_id:
                self.student_current_bloc_id = bloc
                return
        self.student_current_bloc_id = False

    @api.one
    @api.depends('student_bloc_ids')
    def _is_student_registered(self):
        for bloc in self.student_bloc_ids:
            if bloc.year_id == self.env.user.current_year_id:
                self.is_student_registered = True
                return
    
    def _search_student_registered(self, operator, value):
        current_year_id = self.env.user.current_year_id
        year_ids = []
        if 'current' in value:
            year_ids.append(current_year_id.id)
        if 'previous' in value:
            year_ids.append(current_year_id.previous.id)
        if 'next' in value:
            year_ids.append(current_year_id.next.id)
        return [('student_bloc_ids.year_id','in',year_ids)]
    
    @api.one
    def _get_teacher_current_course_session_ids(self):
        res = self.env['school.course_session'].search([['year_id', '=', self.env.user.current_year_id.id], ['teacher_id', '=', self.id]])
        self.teacher_current_assigment_ids = res
    
    # TODO : This is not working but don't know why
    @api.model
    def _get_default_image(self, is_company, colorize=False):
        if getattr(threading.currentThread(), 'testing', False) or self.env.context.get('install_mode'):
            return False

        if self.env.context.get('partner_type') == 'invoice':
            img_path = openerp.modules.get_module_resource('school_management', 'static/src/img', 'home-icon.png')
            with open(img_path, 'rb') as f:
                image = f.read()
            return tools.image_resize_image_big(image.encode('base64'))
        else:
            return super(Partner, self)._get_default_image(is_company, colorize)