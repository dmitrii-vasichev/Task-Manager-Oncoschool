import type { Department, MemberRole } from "./types";

interface DepartmentAccessContext {
  departments: Department[];
  userId: string;
  userRole: MemberRole | "";
  userDepartmentId: string | null;
  userExtraDepartmentIds?: string[];
}

export function getAccessibleDepartments({
  departments,
  userId,
  userRole,
  userDepartmentId,
  userExtraDepartmentIds = [],
}: DepartmentAccessContext): Department[] {
  if (!userId) {
    return [];
  }

  if (userRole === "admin" || userRole === "moderator") {
    return departments;
  }

  const allowedDepartmentIds = new Set<string>();
  if (userDepartmentId) {
    allowedDepartmentIds.add(userDepartmentId);
  }
  for (const departmentId of userExtraDepartmentIds) {
    if (departmentId) {
      allowedDepartmentIds.add(departmentId);
    }
  }

  for (const department of departments) {
    if (department.head_id === userId) {
      allowedDepartmentIds.add(department.id);
    }
  }

  return departments.filter((department) => allowedDepartmentIds.has(department.id));
}
