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

from openerp import api, fields, models, _
from openerp.exceptions import UserError, ValidationError
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

class StatisticTemplate(models.Model):
    '''Statistic Report'''
    _name = 'school.statistic_template'
    
    name = fields.Char(string="Name")
    
    source_model = fields.Char(string='Source Model', required=True, help="Model name of the source object")
    source_domain = fields.Text(string='Domain use to filter source model')
    statistic_field_ids = fields.Many2many('school.statistic_field','statistic_template_field_rel','template_id','field_id',string="Fields")

    def _compute_field_value(self, record, field):
        if field.type == 'F':
            return {
                'field_id': field.id,
                'char_value' : field.fixed_value # TODO : should we handle other type of field ??
            }
        if field.type == 'C':
            if field.value_type == 'C' : 
                return  {
                    'field_id': field.id,    
                    'char_value' : eval(field.compute_expression)
                }
            if field.value_type == 'F' : 
                return  {
                    'field_id': field.id,    
                    'float_value' : eval(field.compute_expression)
                }
            if field.value_type == 'I' : 
                return  {
                    'field_id': field.id,    
                    'integer_value' : eval(field.compute_expression)
                }
            if field.value_type == 'D' : 
                return  {
                    'field_id': field.id,    
                    'date_value' : eval(field.compute_expression) # TODO : encode date ??
                }
        if field.type == 'M':
            return  {
                'field_id': field.id,
            }
        
    @api.multi
    def generate(self):
        self.ensure_one()
        report = self.env['school.statistic_report'].create({
                'template_id' : self.id,
        })
        records = []
        if self.source_domain:
            domain = eval(self.source_domain)
        else:
            domain = []
        _logger.info('Get %s using domain %s' % (self.source_model,domain))
        record_ids = self.env[self.source_model].search(domain)
        for record in record_ids:
            fields = []
            for field in self.statistic_field_ids:
                _logger.info('Append %s' % (self._compute_field_value(record, field)))
                fields.append((0,0,self._compute_field_value(record, field)))
            records.append((0,0,{
                'name': record.name,
                'source_id': record.id,
                'value_ids': fields,
            }))
        report.write({'record_ids': records})
        return {
            'name': _('Statistic Report'),
            'domain': [('template_id', '=', self.id)],
            'res_model': 'school.statistic_report',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_type': 'form',
        }
        
class StatisticField(models.Model):
    '''Statistic Field'''
    _name = 'school.statistic_field'
    
    _order = 'sequence'
    
    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    sequence = fields.Integer(string="Sequence")
    
    type = fields.Selection([('C', 'Computed'),('M', 'Manual'),('F','Fixed')], string='Type of field',default='M')
    
    value_type = fields.Selection([('C', 'Char'),('D', 'Date'),('F','Float'),('I','Integer'),('S','Selection')], string='Type of field',default='C')
    
    compute_expression = fields.Text(string='Compute Expression', help='Compute, record is the current record.')
    fixed_value = fields.Char(string="Fixed Value")
    selection_values = fields.Text(string='Selection Values', help="Comma separated list of values 'aaa','bbb','ccc','dddd'")
    
    statistic_template_ids = fields.Many2many('school.statistic_template','statistic_template_field_rel','field_id','template_id',string="Templates", readonly=True)
    
class StatisticReport(models.Model):
    '''Statistic Field'''
    _name = 'school.statistic_report'
    
    template_id = fields.Many2one('school.statistic_template',string='Template')
    record_ids = fields.One2many('school.statistic_record', 'report_id')
    record_count = fields.Integer(string="Record Count", compute="_compute_count")
    
    @api.one
    @api.depends('record_ids')
    def _compute_count(self):
        self.record_count = len(self.record_ids)
        
class StatisticRecord(models.Model):
    '''Statistic Record'''
    _name = 'school.statistic_record'  

    name = fields.Char(string="Name",readonly=True)    
    source_id = fields.Char(string='Source Id', required=True, help="Id the source object")
    report_id = fields.Many2one('school.statistic_report', readonly=True)
    value_ids = fields.One2many('school.statistic_value', 'record_id', string="Values")
    
class StatisticValue(models.Model):
    '''Statistic Field'''
    _name = 'school.statistic_value'
    _order = 'sequence'
    
    record_id = fields.Many2one('school.statistic_record', readonly=True)
    field_id = fields.Many2one('school.statistic_field', readonly=True)
    
    sequence = fields.Integer(related='field_id.sequence',store=True)
    code = fields.Char(related='field_id.code',store=True)
    name = fields.Char(related='field_id.name',store=True)
    type = fields.Selection(related='field_id.type',store=True)
    value_type = fields.Selection(related='field_id.value_type',store=True)
    
    value = fields.Char(string='Value', compute='_compute_value')
    
    char_value = fields.Char(string="Char Value")
    date_value = fields.Date(string="Date Value")
    float_value = fields.Date(string="Float Value")
    integer_value = fields.Date(string="Integer Value")

    @api.one
    def _compute_selection(self):
        return self.field_id.selection_values

    selection_value = fields.Selection(string="Selection Value", selection=_compute_selection)
    
    @api.depends('value_type','char_value','date_value','float_value','integer_value','selection_value')
    @api.one
    def _compute_value(self):
        if self.value_type == 'C':
            self.value = self.char_value
        elif self.value_type == 'D':
            self.value = self.date_value
        elif self.value_type == 'F':
            self.value = self.float_value
        elif self.value_type == 'I':
            self.value = self.integer_value
        elif self.value_type == 'S':
            self.value = self.selection_value

class StatisticXlsx(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, reports):
        for obj in reports:
            report_name = obj.template_id.name
            sheet = workbook.add_worksheet(report_name[:31])
            bold = workbook.add_format({'bold': True})
            sheet.write(0, 0, obj.template_id.name, bold)

StatisticXlsx('report.statistic_report.xlsx','school.statistic_report')