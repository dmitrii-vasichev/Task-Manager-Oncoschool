import type { Department, MemberRole } from "./types";

interface DepartmentAccessContext {
  departments: Department[];
  userId: string;
  userRole: MemberRole | "";
  userDepartmentId: string | null;
}

export function getAccessibleDepartments({
  departments,
  userId,
  userRole,
  userDepartmentId,
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

  for (const department of departments) {
    if (department.head_id === userId) {
      allowedDepartmentIds.add(department.id);
    }
  }

  return departments.filter((department) => allowedDepartmentIds.has(department.id));
}
