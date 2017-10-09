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

from odoo import api, fields, models, _
from odoo.exceptions import MissingError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

class RegisterNext(models.TransientModel):
    _name = "school.register_next_wizard"
    _description = "Register Next Wizard"
    
    init_bloc_id = fields.Many2one('school.individual_bloc', string="Initial Bloc", required=True, readonly=True, ondelete='cascade')
    year_id = fields.Many2one('school.year', related="init_bloc_id.year_id.next", readonly=True, ondelete='cascade')
    init_source_bloc_name = fields.Char(string="Initial Source Bloc", readonly=True, related="init_bloc_id.source_bloc_name")
    student_id = fields.Many2one('res.partner', related="init_bloc_id.student_id", readonly=True, ondelete='cascade')
    
    new_source_bloc_id = fields.Many2one('school.bloc', string="New Source Bloc", domain="[('year_id','=',year_id)]", ondelete='cascade')

    @api.model
    def default_get(self, fields):
        res = super(RegisterNext, self).default_get(fields)
        # Let's try to guess the next bloc in the program. TODO - could do better than the title, speciality ??
        init_bloc_id = self.env['school.individual_bloc'].browse(res.get('init_bloc_id'))
        res['yeard_id'] = init_bloc_id.year_id.next.id
        if init_bloc_id.state == 'failed':
            new_bloc_source_id = self.env['school.bloc'].search([('year_id','=',init_bloc_id.year_id.next.id),('title', '=', init_bloc_id.source_bloc_title),('level','=',int(init_bloc_id.source_bloc_id.level))])
        else:
            new_bloc_source_id = self.env['school.bloc'].search([('year_id','=',init_bloc_id.year_id.next.id),('title', '=', init_bloc_id.source_bloc_title),('level','=',int(init_bloc_id.source_bloc_id.level)+1)])
        if new_bloc_source_id:
            res['new_source_bloc_id'] = new_bloc_source_id[0].id
        return res
    
    @api.multi
    def on_confirm_source(self):
        new_bloc = self.env['school.individual_bloc'].create({'year_id':self.init_bloc_id.year_id.next.id,'student_id': self.init_bloc_id.student_id.id,'source_bloc_id':self.new_source_bloc_id.id,'program_id':self.init_bloc_id.program_id.id})
        new_bloc.assign_source_bloc()
        self.new_bloc_id = new_bloc

        # Previous year was not a success, we try to find "dispense" automatically
        if self.init_bloc_id.source_bloc_level == new_bloc.source_bloc_level:
            for group in self.init_bloc_id.course_group_ids:
                if group.acquiered == 'A':
                    # TODO : we already have the list, why a query ??
                    new_group = self.env['school.individual_course_group'].search([('bloc_id','=',new_bloc.id),('source_course_group_id','=',group.source_course_group_id.id)])
                    if new_group:
                        for index, new_course in enumerate(new_group.course_ids):
                            _logger.debug("Set a dispense on %s",new_course.name)
                            old_course = group.course_ids[index]
                            if old_course.second_session_result_bool:
                                res = old_course.second_session_result
                            else:
                                res = old_course.first_session_result
                            new_course.dispense = True
                            new_course.jun_result = res

        # Previous year was a succes, we try to find if some CG was not acquiered and add them
        else :
            for group in self.init_bloc_id.course_group_ids:
                if group.acquiered == 'NA':
                    # check if the group is already present (an anticipated cg that was not acquiered)
                    new_group = self.env['school.individual_course_group'].search([('bloc_id','=',new_bloc.id),('source_course_group_id','=',group.source_course_group_id.id)])
                    if not new_group:
                        new_group = self.new_bloc_id.course_group_ids.create({'bloc_id': self.new_bloc_id.id,'source_course_group_id': group.source_course_group_id.id, 'acquiered' : 'NA', 'dispense': False, 'group_registration_type' : 'rework'})
                        new_group.onchange_source_cg()
                        for index, new_course in enumerate(new_group.course_ids):
                            old_course = group.course_ids[index]
                            if old_course.teacher_id:
                                new_course.teacher_id = old_course.teacher_id
                        
        # Find in student history if erver one course_group was already acquiered
        
        for new_group in new_bloc.course_group_ids:
            for index, new_course in enumerate(new_group.course_ids):
                changed = False
                old_course = self.env['school.individual_course'].search([('student_id','=',new_group.student_id.id),('source_course_id','=',new_course.source_course_id.id),'|',('first_session_result','>=',10),('second_session_result','>=',10)])
                if old_course:
                    old_course =  old_course[0] # could happen there is multiple reports
                    if old_course.second_session_result_bool:
                        res = old_course.second_session_result
                    else:
                        res = old_course.first_session_result
                    changed = True
                    new_course.dispense = True
                    new_course.is_dispense_approved = True
                    new_course.jun_result = res
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'school.individual_bloc',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.new_bloc_id.id,
            'views': [(False, 'form')],
        }

            
class AddAnticipatedWizard(models.TransientModel):
    _name = "school.add_anticipated_wizard"
    _description = "Add Anticipated Wizard"
    
    init_bloc_id = fields.Many2one('school.individual_bloc', string="Initial Bloc", required=True, readonly=True, ondelete='cascade')
    year_id = fields.Many2one('school.year', related="init_bloc_id.year_id", readonly=True, ondelete='cascade')
    init_source_bloc_name = fields.Char(string="Initial Source Bloc", readonly=True, related="init_bloc_id.source_bloc_name", ondelete='cascade')
    student_id = fields.Many2one('res.partner', related="init_bloc_id.student_id", readonly=True, ondelete='cascade')
    
    course_group_ids = fields.Many2many('school.course_group', string='New Source Course Group') # TODO add a domain to filter??
    
    @api.model
    def default_get(self, fields):
        res = super(AddAnticipatedWizard, self).default_get(fields)
        # Let's try to guess the next bloc in the program. TODO - could do better than the title, speciality ??
        init_bloc_id = self.env['school.individual_bloc'].browse(res.get('init_bloc_id'))
        res['yeard_id'] = init_bloc_id.year_id.next.id
        return res
        
    @api.multi
    def on_add_anticipated(self):
        for group in self.course_group_ids:
            new_group = self.init_bloc_id.course_group_ids.create({'bloc_id': self.init_bloc_id.id,'source_course_group_id': group.id, 'acquiered' : 'NA', 'dispense': False, 'group_registration_type' : 'anticipated'})
            new_group.onchange_source_cg()