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

_logger = logging.getLogger(__name__)

class Etablissement(models.Model):
    '''Etablissement'''
    _name = 'school.stat_etablissement'
    
    name = fields.Char(string="Name")
    code_fase = fields.Char(string="Code FASE")
    
class Domaine(models.Model):
    '''Domaine'''
    _name = 'school.stat_domain'
    
    name = fields.Char(string="Name")
    code = fields.Char(string="Code")

class Partner(models.Model):
    '''Partner'''
    _inherit = 'res.partner'

    student_historic_entry_ids = fields.One2many('school.student_history_entry', 'student_id', string="Student History Entries", track_visibility='onchange')

class StudentHistoryEntry(models.Model):
    '''Student History Entry'''
    _name = 'school.student_history_entry'
    
    year_id = fields.Many2one('school.year', string="Year", required=True)
    student_id = fields.Many2one('res.partner', string="Student", required=True)
    activite = fields.Selection([
        ('1','Enseignement secondaire non obligatoire (année préparatoire à l’enseignement supérieur, 4e cycle du secondaire, ...)'),
        ('2','Haute École de la Fédération Wallonie‐Bruxelles ou germanophone'),
        ('3','Université de la Fédération Wallonie‐Bruxelles'),
        ('4','Institut supérieur d''Architecture de la Fédération Wallonie‐Bruxelles'),
        ('5','École supérieure des Arts de la Fédération Wallonie‐Bruxelles'),
        ('6','Enseignement supérieur de promotion sociale de la Fédération Wallonie‐Bruxelles'),
        ('7','Enseignement supérieur de la Communauté flamande'),
        ('8','Enseignement supérieur à l''étranger'),
        ('9','Travail rémunéré'),
        ('10','Chômage'),
        ('11','Autre (année sabbatique, préparation à l''enseignement supérieur autre que dans le cadre de l''enseignement secondaire,...)'),
        ], string="Activité", required=True)
    etablissement_id = fields.Many2one('school.stat_etablissement', string="Etablissement", required=True)
    domain_id = fields.Many2one('school.stat_domain', string="Domaine", required=True)
    annee = fields.Selection([
            ('11','1re Bac'),
            ('12','2e Bac'),
            ('13','3e Bac'),
            ('14','4e Bac'),
            ('21','1re Master'),
            ('22','2e Master'),
            ('23','3e Master'),
            ('24','4e Master'),
            ('31','1re Spécialisation'),
            ('32','2e Spécialisation'),
            ('40','Doctorat'),
            ('99','Autres (CAPAES, AESS, Année préparatoire, etc.)'),
        ], string="Année", required=True)
    resultat = fields.Selection([
            ('1','Réussite'),
            ('2','Refusé'),
        ],string="Résultat", required=True)

class Domain(models.Model):
    '''Domain'''
    _inherit = 'school.domain'

    saturn_code = fields.Char(string="Saturn Code")

class Section(models.Model):
    '''Section'''
    _inherit = 'school.section'

    saturn_code = fields.Char(string="Saturn Code")

class Track(models.Model):
    '''Track'''
    _inherit = 'school.track'

    saturn_code = fields.Char(string="Saturn Code")

class Speciality(models.Model):
    '''Speciality'''
    _inherit = 'school.speciality'

    saturn_code = fields.Char(string="Saturn Code")