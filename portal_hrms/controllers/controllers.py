# -*- coding: utf-8 -*-

from odoo import fields
from dateutil.relativedelta import relativedelta
from odoo.tools import date_utils, groupby
from odoo import http, _
from operator import itemgetter
from pytz import timezone, UTC
from odoo.addons.resource.models.resource import float_to_time
from collections import OrderedDict
from collections import namedtuple
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.http import request
from odoo.osv.expression import OR
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime
from odoo.tools import groupby as groupbyelem

class CustomerPortalInherit(CustomerPortal):

    def _prepare_portal_layout_values(self):
        data = super()._prepare_portal_layout_values()
        omni_employee_id = request.env.user.employee_id
        omni_attendance_rec = request.env['hr.attendance'].sudo().search([('employee_id', '=', omni_employee_id.id)],
                                                                         limit=1)

        if omni_attendance_rec:
            data.update({
                'omni_employee_id': omni_employee_id.name,
                'omni_check_out': omni_attendance_rec.check_out,
            })
        else:
            data.update({
                'omni_employee_id': omni_employee_id.name,
                'omni_check_out': True,
            })
        return data

    def filter_data(self, filter_one, filter_two):
        omni_employee_id = request.env.user.employee_id
        omni_date1 = datetime.strftime(filter_one, "%Y-%m-%d %H:%M:%S")
        omni_date2 = datetime.strftime(filter_two, "%Y-%m-%d 23:59:59")
        self.attendance_rec = request.env['hr.attendance'].sudo().search(
            [('employee_id', '=', omni_employee_id.id), ('check_in', '>=', omni_date1), ('check_in', '<=', omni_date2)])
        return self.attendance_rec

    def _get_searchbar_input(self):
        return {
            'all': {'input': 'all', 'label': _('Search in All')},
            'check_in': {'input': 'check_in', 'label': _('Search in Check In')},
            'check_out': {'input': 'check_out', 'label': _('Search in Check Out')},
            # 'worked_hours': {'input': 'worked_hours', 'label': _('Search in Worked Hours')}
        }

    def _get_search_domain(self, search_in, search):
        search_domain = []
        if search_in in ('check_in', 'all'):
            search_domain = OR([search_domain, [('check_in', 'ilike', search)]])
        if search_in in ('check_out', 'all'):
            search_domain = OR([search_domain, [('check_out', 'ilike', search)]])
        # if search_in in ('worked_hours', 'all'):
        #     search_domain = OR([search_domain, [('worked_hours', 'ilike', search)]])
        return search_domain

    @http.route(['/omni/my/attendance'], type='http', auth="user", website=True)
    def portal_my_attendance(self):
        values = self._prepare_portal_layout_values()
        omni_employee_id = request.env.user.employee_id
        omni_attendance_rec = request.env['hr.attendance'].sudo().search([('employee_id', '=', omni_employee_id.id)], limit=1)
        values.update({
            'omni_employee_id': omni_employee_id.name,
            'image_1920': omni_employee_id.image_1920 or omni_employee_id.company_id.logo,
            'page_name': 'attendance',
            'worked_hours': omni_employee_id.hours_today,
        })
        if omni_attendance_rec:
            values.update({'check_out': omni_attendance_rec.check_out, 'check_in_time': omni_attendance_rec.check_in, })
        else:
            values.update({'check_in_time': datetime.now(), 'not_check_in': True, })

        return request.render("portal_hrms.attendance_home", values)

    @http.route(['/omni/my/attendance/list_view'], type='http', auth="user", website=True)
    def list_method(self, page=1, sortby=None, filterby=None, search=None, search_in='all', groupby='none', **kw):
        values = self._prepare_portal_layout_values()
        omni_employee_id = request.env.user.employee_id
        domain = [request.env['hr.attendance'].sudo().search([('employee_id', '=', omni_employee_id.id)])]

        searchbar_inputs = self._get_searchbar_input()

        today = fields.Date.today()
        quarter_start, quarter_end = date_utils.get_quarter(today)
        last_week = today + relativedelta(weeks=-1)
        last_month = today + relativedelta(months=-1)
        last_year = today + relativedelta(years=-1)

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'today': {'label': _('Today'), 'domain': [("date", "=", today)]},
            'week': {'label': _('This week'), 'domain': [('date', '>=', date_utils.start_of(today, "week")),
                                                         ('date', '<=', date_utils.end_of(today, 'week'))]},
            'month': {'label': _('This month'), 'domain': [('date', '>=', date_utils.start_of(today, 'month')),
                                                           ('date', '<=', date_utils.end_of(today, 'month'))]},
            'year': {'label': _('This year'), 'domain': [('date', '>=', date_utils.start_of(today, 'year')),
                                                         ('date', '<=', date_utils.end_of(today, 'year'))]},
            'quarter': {'label': _('This Quarter'),
                        'domain': [('date', '>=', quarter_start), ('date', '<=', quarter_end)]},
            'last_week': {'label': _('Last week'), 'domain': [('date', '>=', date_utils.start_of(last_week, "week")),
                                                              ('date', '<=', date_utils.end_of(last_week, 'week'))]},
            'last_month': {'label': _('Last month'),
                           'domain': [('date', '>=', date_utils.start_of(last_month, 'month')),
                                      ('date', '<=', date_utils.end_of(last_month, 'month'))]},
            'last_year': {'label': _('Last year'), 'domain': [('date', '>=', date_utils.start_of(last_year, 'year')),
                                                              ('date', '<=', date_utils.end_of(last_year, 'year'))]},
        }

        if not filterby:
            filterby = 'all'

        all_data = []
        data = {}
        omni_employee_id = request.env.user.employee_id

        if filterby == 'all':
            self.attendance_rec = request.env['hr.attendance'].sudo().search([('employee_id', '=', omni_employee_id.id)])
        elif filterby == 'today':
            self.filter_data(filter_one=today, filter_two=today)
        elif filterby == 'last_month':
            self.filter_data(filter_one=date_utils.start_of(last_month, 'month'),
                             filter_two=date_utils.end_of(last_month, 'month'))
        elif filterby == 'last_week':
            self.filter_data(filter_one=date_utils.start_of(last_week, 'week'),
                             filter_two=date_utils.end_of(last_week, 'week'))
        elif filterby == 'last_year':
            self.filter_data(filter_one=date_utils.start_of(last_year, 'year'),
                             filter_two=date_utils.end_of(last_year, 'year'))
        elif filterby == 'month':
            self.filter_data(filter_one=date_utils.start_of(today, 'month'),
                             filter_two=date_utils.end_of(today, 'month'))
        elif filterby == 'quarter':
            self.filter_data(filter_one=quarter_start, filter_two=quarter_end)
        elif filterby == 'week':
            self.filter_data(filter_one=date_utils.start_of(today, 'week'), filter_two=date_utils.end_of(today, 'week'))
        elif filterby == 'year':
            self.filter_data(filter_one=date_utils.start_of(today, 'year'), filter_two=date_utils.end_of(today, 'year'))

        if search:
            if search_in == 'check_in':
                omni_employee_id = request.env.user.employee_id
                self.attendance_rec = request.env['hr.attendance'].sudo().search(
                    [('employee_id', '=', omni_employee_id.id), ("check_in", "ilike", search)])
            elif search_in == 'check_out':
                omni_employee_id = request.env.user.employee_id
                self.attendance_rec = request.env['hr.attendance'].sudo().search(
                    [('employee_id', '=', omni_employee_id.id), ("check_out", "ilike", search)])
            elif search_in == 'all':
                omni_employee_id = request.env.user.employee_id
                self.attendance_rec = request.env['hr.attendance'].sudo().search(
                    [('employee_id', '=', omni_employee_id.id), '|', ("check_in", "ilike", search), '|',
                     ("check_out", "ilike", search), ("worked_hours", "ilike", search)])

        for rec in self.attendance_rec:
            all_data.append(
                {'employee_name': rec.employee_id.name, 'check_in': rec.check_in, 'check_out': rec.check_out,
                 'worked_hours': rec.worked_hours})

        data = {
            'key': all_data
        }
        data.update({
            'page_name': 'list_view',
            'default_url': '/omni/my/attendance/list_view',
            'search_in': search_in,
            'search': search,
            'sortby': sortby,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return request.render("portal_hrms.attendance_list_view", data)

    @http.route(['/omni/my/attendance/update'], type='json', auth="user", methods=['POST'], website=True, csrf=False)
    def update_status(self, display=True):

        values = self._prepare_portal_layout_values()
        employee_id = request.env.user.employee_id
        attendance_rec = request.env['hr.attendance'].sudo().search([('employee_id', '=', employee_id.id)], limit=1)

        if attendance_rec:
            if attendance_rec.check_out:
                attendance_rec.create({'check_in': datetime.now(), })
            else:
                attendance_rec.sudo().update({'check_out': datetime.now(), })
        else:
            attendance_rec.create({'check_in': datetime.now(), })

        return {}





DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period, week_type')


class PortalLeaveKnk(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if request.env.user._is_admin():
            domain = []
        else:
            domain = [('employee_id', '=', request.env.user.employee_id.id)]
        if 'leave_count' in counters:
            leave_count = request.env['hr.leave'].search_count(domain) \
                if request.env['hr.leave'].check_access_rights('read', raise_exception=False) else 0
            values['leave_count'] = leave_count
        return values

    def _get_searchbar_inputs(self):
        return {
            'all': {'input': 'all', 'label': _('Search in All')},
            'employee': {'input': 'employee', 'label': _('Search in Employee')},
            'leave_type': {'input': 'leave_type', 'label': _('Search in Leave Type')},
            'reason': {'input': 'reason', 'label': _('Search in Reason')},
        }

    def _get_search_domain(self, search_in, search):
        search_domain = []
        if search_in in ('name', 'all'):
            search_domain = OR([search_domain, [('name', 'ilike', search)]])
        if search_in in ('employee', 'all'):
            search_domain = OR([search_domain, [('employee_id', 'ilike', search)]])
        if search_in in ('leave_type', 'all'):
            search_domain = OR([search_domain, [('holiday_status_id', 'ilike', search)]])
        if search_in in ('reason', 'all'):
            search_domain = OR([search_domain, [('name', 'ilike', search)]])
        return search_domain

    def _get_searchbar_sortings(self):
        return {
            'date_from': {'label': _('Start Date'), 'order': 'date_from desc', 'sequence': 1},
            'date_to': {'label': _('End Date'), 'order': 'date_to desc', 'sequence': 2},
            'leave_type': {'label': _('Leave Type'), 'order': 'holiday_status_id', 'sequence': 3},
            'status': {'label': _('Status'), 'order': 'state', 'sequence': 4},
        }

    def _get_searchbar_groupby(self):
        values = {
            'none': {'input': 'none', 'label': _('None'), 'order': 1},
            'leave_type': {'input': 'leave_type', 'label': _('Leave Type'), 'order': 2},
            'status': {'input': 'status', 'label': _('Status'), 'order': 3},
        }
        return dict(sorted(values.items(), key=lambda item: item[1]["order"]))

    def _get_groupby_mapping(self):
        return {
            'leave_type': 'holiday_status_id',
            'status': 'state',
        }

    def _get_order(self, order, groupby):
        groupby_mapping = self._get_groupby_mapping()
        field_name = groupby_mapping.get(groupby, '')
        if not field_name:
            return order
        return '%s, %s' % (field_name, order)

    @http.route(['/my/leaves', '/my/leaves/page/<int:page>'], type='http', auth="user", website=True)
    def portal_payslip(self, page=1, sortby=None, filterby=None, search=None, search_in='all', groupby=None, **kw):
        values = self._prepare_portal_layout_values()
        Leave = request.env['hr.leave']
        _items_per_page = 20

        if request.env.user._is_admin():
            domain = []
        else:
            domain = [('employee_id', '=', request.env.user.employee_id.id)]
        searchbar_sortings = self._get_searchbar_sortings()
        searchbar_groupby = self._get_searchbar_groupby()
        searchbar_inputs = self._get_searchbar_inputs()
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': domain},
            'approved': {'label': _('Approved Time Off'), 'domain': [('state', '=', 'validate')]},
            'to_approve': {'label': _('To Approve'), 'domain': [('state', '=', 'confirm')]},
        }

        if not sortby:
            sortby = 'date_from'
        order = searchbar_sortings[sortby]['order']

        if not filterby:
            filterby = 'all'
        domain += searchbar_filters.get(filterby, searchbar_filters.get('all'))['domain']

        if not groupby:
            groupby = 'none'

        if search and search_in:
            domain += self._get_search_domain(search_in, search)

        leave_count = Leave.search_count(domain)

        pager = portal_pager(
            url="/my/leaves",
            url_args={'search_in': search_in, 'search': search, 'groupby': groupby, 'filterby': filterby, 'sortby': sortby},
            total=leave_count,
            page=page,
            step=_items_per_page
        )

        order = self._get_order(order, groupby)
        leaves = Leave.search(domain, order=order, limit=_items_per_page, offset=pager['offset'])
        request.session['my_leave_history'] = leaves.ids[:100]

        groupby_mapping = self._get_groupby_mapping()
        group = groupby_mapping.get(groupby)
        if group:
            grouped_leaves = [Leave.concat(*g) for k, g in groupbyelem(leaves, itemgetter(group))]
        else:
            grouped_leaves = [leaves]

        allocations = request.env['hr.leave.allocation'].search([('employee_id', '=', request.env.user.employee_id.id), ('state', '=', 'validate')])
        allocation_data = allocations.holiday_status_id.get_days_all_request()
        leave_allocations = {}
        for data in allocation_data:
            leave_allocations[data[0]] = [data[1]['virtual_remaining_leaves'], data[1]['request_unit']]
        values.update({
            'grouped_leaves': grouped_leaves,
            'page_name': 'leave',
            'pager': pager,
            'default_url': '/my/leaves',
            'search_in': search_in,
            'search': search,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_groupby': searchbar_groupby,
            'sortby': sortby,
            'groupby': groupby,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'allocations': leave_allocations,
        })
        return request.render("portal_hrms.portal_my_leave_list", values)

    @http.route(['/create/leave'], type='http', auth="user", website=True)
    def apply_leave(self, **post):
        employee = request.env.user.employee_id
        domain = ['|', ('requires_allocation', '=', 'no'), '&', ('has_valid_allocation', '=', True), '&', ('virtual_remaining_leaves', '>', 0), ('max_leaves', '>', '0')]
        leave_type = request.env['hr.leave.type'].search(domain)
        values = {
            'employee': employee,
            'leave_types': leave_type,
            'page_name': 'create_leave',
        }
        return request.render("portal_hrms.portal_apply_leave", values)

    @http.route(['/save/leave'], type='http', auth="user", website=True)
    def save_leave(self, **post):
        field_list = ['start_date', 'end_date', 'reason', 'leave_type']
        value = []
        domain = ['|', ('requires_allocation', '=', 'no'), '&', ('has_valid_allocation', '=', True), '&', ('virtual_remaining_leaves', '>', 0), ('max_leaves', '>', '0')]
        leave_type = request.env['hr.leave.type'].search(domain)
        start_date = datetime.strptime(post.get('start_date'), DF)
        end_date = datetime.strptime(post.get('end_date'), DF)
        employee = request.env.user.employee_id
        for key in post:
            value.append(post[key])
        if any([field not in post.keys() for field in field_list]) or not all(value) or not post:
            post.update({
                'employee': employee,
                'leave_types': leave_type,
                'page_name': 'create_leave',
                'error': 'Some Required Fields are Missing.'
            })
            return request.render("portal_hrms.portal_apply_leave", post)
        resource_calendar_id = employee.resource_calendar_id
        domain_1 = [('calendar_id', '=', resource_calendar_id.id), ('display_type', '=', False)]
        attendances = request.env['resource.calendar.attendance'].read_group(domain_1, ['ids:array_agg(id)', 'hour_from:min(hour_from)', 'hour_to:max(hour_to)', 'week_type', 'dayofweek', 'day_period'], ['week_type', 'dayofweek', 'day_period'], lazy=False)
        attendances = sorted([DummyAttendance(group['hour_from'], group['hour_to'], group['dayofweek'], group['day_period'], group['week_type']) for group in attendances], key=lambda att: (att.dayofweek, att.day_period != 'morning'))
        default_value = DummyAttendance(0, 0, 0, 'morning', False)
        attendance_from = next((att for att in attendances if int(att.dayofweek) >= start_date.weekday()), attendances[0] if attendances else default_value)
        attendance_to = next((att for att in reversed(attendances) if int(att.dayofweek) <= end_date.weekday()), attendances[-1] if attendances else default_value)
        hour_from = float_to_time(attendance_from.hour_from)
        hour_to = float_to_time(attendance_to.hour_to)
        start_date = timezone(employee.tz).localize(datetime.combine(start_date, hour_from)).astimezone(UTC).replace(tzinfo=None)
        end_date = timezone(employee.tz).localize(datetime.combine(end_date, hour_to)).astimezone(UTC).replace(tzinfo=None)
        error = False
        employee = request.env.user.employee_id
        if start_date.date() > end_date.date():
            error = 'The start date must be anterior to the end date.'

        domain = [
            ('date_from', '<', end_date),
            ('date_to', '>', start_date),
            ('employee_id', '=', employee.id),
            ('state', 'not in', ['cancel', 'refuse']),
        ]
        nholidays = request.env['hr.leave'].search(domain)
        if nholidays:
            error = 'You can not set 2 time off that overlaps on the same day for the same employee.'
        if error:
            post = {'employee': employee,
                    'leave_types': leave_type,
                    'page_name': 'create_leave',
                    'error': error}
            return request.render("portal_hrms.portal_apply_leave", post)

        vals = {
            'employee_id': request.env.user.employee_id.id,
            'holiday_status_id': int(post.get('leave_type')),
            'date_from': start_date,
            'request_date_from': start_date,
            'request_date_to': end_date,
            'date_to': end_date,
            'name': post.get('reason'),
        }
        request.env['hr.leave'].create(vals)
        return request.redirect('/my/leaves')
