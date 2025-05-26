import React, { useState } from 'react';
import { Settings, User, Key, Save, Eye, EyeOff } from 'lucide-react';
import { useAuth } from './AuthContext';

const SettingsPage = () => {
  const { user, updateProfile } = useAuth();
  const [formData, setFormData] = useState({
    email: user?.email || '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    // Validate passwords if changing
    if (formData.newPassword) {
      if (formData.newPassword !== formData.confirmPassword) {
        setMessage('New passwords do not match');
        setLoading(false);
        return;
      }
      if (formData.newPassword.length < 6) {
        setMessage('Password must be at least 6 characters long');
        setLoading(false);
        return;
      }
    }

    const updateData = {
      email: formData.email !== user.email ? formData.email : undefined,
      password: formData.newPassword || undefined
    };

    // Remove undefined values
    Object.keys(updateData).forEach(key => 
      updateData[key] === undefined && delete updateData[key]
    );

    if (Object.keys(updateData).length === 0) {
      setMessage('No changes to save');
      setLoading(false);
      return;
    }

    const result = await updateProfile(updateData);
    
    if (result.success) {
      setMessage('Profile updated successfully!');
      setFormData({
        ...formData,
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
    } else {
      setMessage(result.error || 'Failed to update profile');
    }
    
    setLoading(false);
  };

  const togglePasswordVisibility = (field) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <Settings className="w-8 h-8 text-blue-400" />
        <h2 className="text-2xl font-bold text-white">Account Settings</h2>
      </div>

      {/* User Info Card */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
        <div className="flex items-center space-x-4 mb-4">
          <div className="w-16 h-16 bg-slate-600 rounded-full flex items-center justify-center">
            <User className="w-8 h-8 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-semibold text-white">{user?.email}</h3>
            <p className="text-slate-400 capitalize">{user?.role} Account</p>
            <p className="text-slate-500 text-sm">
              Member since {new Date(user?.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>

      {/* Settings Form */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-6">Update Profile</h3>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {message && (
            <div className={`rounded-lg p-3 ${
              message.includes('successfully') 
                ? 'bg-green-500/10 border border-green-500/30 text-green-400' 
                : 'bg-red-500/10 border border-red-500/30 text-red-400'
            }`}>
              {message}
            </div>
          )}

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your email"
            />
          </div>

          {/* Password Section */}
          <div className="border-t border-slate-600 pt-6">
            <div className="flex items-center space-x-2 mb-4">
              <Key className="w-5 h-5 text-slate-400" />
              <h4 className="text-white font-medium">Change Password</h4>
              <span className="text-slate-400 text-sm">(Optional)</span>
            </div>

            {/* Current Password */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Current Password
              </label>
              <div className="relative">
                <input
                  type={showPasswords.current ? 'text' : 'password'}
                  value={formData.currentPassword}
                  onChange={(e) => setFormData({ ...formData, currentPassword: e.target.value })}
                  className="w-full px-3 py-3 pr-10 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter current password"
                />
                <button
                  type="button"
                  onClick={() => togglePasswordVisibility('current')}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-300"
                >
                  {showPasswords.current ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* New Password */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                New Password
              </label>
              <div className="relative">
                <input
                  type={showPasswords.new ? 'text' : 'password'}
                  value={formData.newPassword}
                  onChange={(e) => setFormData({ ...formData, newPassword: e.target.value })}
                  className="w-full px-3 py-3 pr-10 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter new password"
                />
                <button
                  type="button"
                  onClick={() => togglePasswordVisibility('new')}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-300"
                >
                  {showPasswords.new ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* Confirm Password */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Confirm New Password
              </label>
              <div className="relative">
                <input
                  type={showPasswords.confirm ? 'text' : 'password'}
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                  className="w-full px-3 py-3 pr-10 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Confirm new password"
                />
                <button
                  type="button"
                  onClick={() => togglePasswordVisibility('confirm')}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-300"
                >
                  {showPasswords.confirm ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>
          </div>

          {/* Save Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white py-3 rounded-lg font-semibold transition-colors duration-200 flex items-center justify-center space-x-2"
          >
            <Save className="w-5 h-5" />
            <span>{loading ? 'Saving...' : 'Save Changes'}</span>
          </button>
        </form>
      </div>

      {/* Security Notice */}
      <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600">
        <h4 className="text-white font-medium mb-2">Security Notice</h4>
        <ul className="text-slate-300 text-sm space-y-1">
          <li>• Use a strong password with at least 8 characters</li>
          <li>• Include a mix of letters, numbers, and symbols</li>
          <li>• Don't reuse passwords from other accounts</li>
          <li>• Contact your administrator if you suspect unauthorized access</li>
        </ul>
      </div>
    </div>
  );
};

export default SettingsPage;