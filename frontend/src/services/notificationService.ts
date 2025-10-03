import { api, apiConfig } from '@/config/api';

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  data?: any;
  created_at: string;
}

export interface ApiResponse {
  success: boolean;
  message: string;
  data?: any;
}

export const notificationService = {
  // Get notifications for current user
  async getUserNotifications(): Promise<Notification[]> {
    try {
      const userId = localStorage.getItem('preklo_user_id');
      if (!userId) {
        throw new Error('User ID not found');
      }

      const response = await api.get<Notification[]>(
        `${apiConfig.endpoints.notifications}/user/${userId}`
      );
      return response;
    } catch (error) {
      console.error('Failed to get notifications:', error);
      throw error;
    }
  },

  // Mark a notification as read
  async markNotificationAsRead(notificationId: string): Promise<ApiResponse> {
    try {
      const response = await api.put<ApiResponse>(
        `${apiConfig.endpoints.notifications}/${notificationId}/read`
      );
      return response;
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
      throw error;
    }
  },

  // Mark all notifications as read
  async markAllNotificationsAsRead(): Promise<ApiResponse> {
    try {
      const userId = localStorage.getItem('preklo_user_id');
      if (!userId) {
        throw new Error('User ID not found');
      }

      const response = await api.put<ApiResponse>(
        `${apiConfig.endpoints.notifications}/user/${userId}/read-all`
      );
      return response;
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
      throw error;
    }
  },

  // Get unread notification count
  async getUnreadCount(): Promise<number> {
    try {
      const notifications = await this.getUserNotifications();
      return notifications.filter(n => !n.is_read).length;
    } catch (error) {
      console.error('Failed to get unread count:', error);
      return 0;
    }
  }
};
