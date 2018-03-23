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
from openerp.exceptions import MissingError

_logger = logging.getLogger(__name__)

class BookingWizard(models.TransientModel):
    _name = "school.school_booking_wizard"
    _description = "School Booking Wizard"
    
    room_ids = fields.Many2many('school.asset', 'booking_wizard_room_ref', 'wizard_id', 'room_id', string='Rooms', domain="[('is_room','=',True)]")
    
    from_date = fields.Datetime('From Date')
    to_date = fields.Datetime('From Date')
    
    @api.one
    @api.depends('from_date', 'to_date')
    def find_rooms(self):
        if self.from_date and self.to_date :
            the_fields = ['name','room_id']
            domain = [
                ('start', '<', self.to_date),    
                ('stop', '>', self.from_date),
                ('room_id', '<>', False),
            ]
            all_rooms_ids = self.env['school.asset'].search( [['asset_type_id.is_room','=',True]] )
            busy_rooms_ids = self.env['calendar.event'].sudo().with_context({'virtual_id': True}).search(domain,the_fields)
            busy_rooms_ids = busy_rooms_ids.filtered(lambda r : r.start_datetime < self.to_date).filtered(lambda r : r.stop_datetime > self.from_date).mapped('room_id')
            self.room_ids = all_rooms_ids - busy_rooms_ids
        
    @api.one
    @api.depends('from_date', 'to_date')
    def create_booking(self):
        pass