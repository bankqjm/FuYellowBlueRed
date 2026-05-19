export const ROLE_MAP: Record<string, { text: string; color: string }> = {
  USER: { text: '普通用户', color: 'blue' },
  SHOP_OWNER: { text: '商家', color: 'green' },
  RIDER: { text: '骑手', color: 'orange' },
  ADMIN: { text: '管理员', color: 'red' },
}

export const getRoleName = (role: string | undefined | null): string => {
  if (!role) {return '未知'}
  return ROLE_MAP[role]?.text || role
}

export const getRoleInfo = (role: string | undefined | null): { text: string; color: string } => {
  if (!role) {return { text: '未知', color: 'default' }}
  return ROLE_MAP[role] || { text: role, color: 'default' }
}
