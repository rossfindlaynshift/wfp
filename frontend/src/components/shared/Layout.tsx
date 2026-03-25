import { NavLink, Outlet } from 'react-router-dom';
import {
  DollarSign, Building2, GitBranch, UserX, TrendingUp,
  Target, CalendarClock, Briefcase, LayoutDashboard,
} from 'lucide-react';

const refLinks = [
  { to: '/ref/fx-rates', label: 'FX Rates', icon: DollarSign },
  { to: '/ref/loading-multipliers', label: 'Loading Multipliers', icon: Building2 },
  { to: '/ref/department-hierarchy', label: 'Dept Hierarchy', icon: GitBranch },
  { to: '/ref/employee-exclusions', label: 'Employee Exclusions', icon: UserX },
  { to: '/ref/merit-assumptions', label: 'Merit Assumptions', icon: TrendingUp },
  { to: '/ref/budget-targets', label: 'Budget Targets', icon: Target },
  { to: '/ref/quota-ramp', label: 'Quota Ramp', icon: CalendarClock },
  { to: '/ref/leave-cost-rates', label: 'Leave Cost Rates', icon: Briefcase },
];

export function Layout() {
  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <nav className="w-64 bg-gray-900 text-gray-300 flex flex-col flex-shrink-0">
        <div className="p-4 border-b border-gray-700">
          <h1 className="text-lg font-bold text-white">Workforce Planning</h1>
        </div>

        <div className="flex-1 overflow-y-auto py-2">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex items-center gap-2 px-4 py-2 text-sm hover:bg-gray-800 ${isActive ? 'bg-gray-800 text-white' : ''}`
            }
          >
            <LayoutDashboard size={16} /> Overview
          </NavLink>

          <div className="px-4 pt-4 pb-1 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Reference Tables
          </div>
          {refLinks.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-2 px-4 py-2 text-sm hover:bg-gray-800 ${isActive ? 'bg-gray-800 text-white' : ''}`
              }
            >
              <Icon size={16} /> {label}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Main content */}
      <main className="flex-1 overflow-auto bg-gray-50">
        <Outlet />
      </main>
    </div>
  );
}
