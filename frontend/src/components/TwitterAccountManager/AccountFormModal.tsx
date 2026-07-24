interface LookupResult {
  exists: boolean;
  user?: {
    username: string;
    name: string;
    profile_image_url?: string | null;
    followers_count?: number | null;
  };
  error?: string;
}

interface AccountFormData {
  username: string;
  display_name: string;
  category: string;
  description: string;
  tier: number;
  enabled: boolean;
}

const CATEGORIES = [
  'AI Company',
  'AI Research',
  'AI Education',
  'AI Tools',
  'AI Leadership',
  'AI Community',
  'AI Applications',
  'Conference',
  'PhD Student',
  'Asst Prof',
  'Other'
];

interface AccountFormModalProps {
  mode: 'add' | 'edit';
  data: AccountFormData;
  onChange: (updater: (prev: AccountFormData) => AccountFormData) => void;
  onSubmit: () => void;
  onCancel: () => void;
  submitting: boolean;
  // Add-mode specific
  onLookup?: () => void;
  lookingUp?: boolean;
  lookupResult?: LookupResult | null;
  // Edit-mode specific
  editUsername?: string;
}

export function AccountFormModal({
  mode,
  data,
  onChange,
  onSubmit,
  onCancel,
  submitting,
  onLookup,
  lookingUp,
  lookupResult,
  editUsername,
}: AccountFormModalProps) {
  const isAdd = mode === 'add';
  const title = isAdd ? 'Add Twitter Account' : `Edit @${editUsername}`;
  const submitLabel = isAdd
    ? (submitting ? 'Adding...' : 'Add Account')
    : (submitting ? 'Saving...' : 'Save Changes');
  const isSubmitDisabled = isAdd
    ? (submitting || !data.username)
    : submitting;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-xl font-bold mb-4">{title}</h2>

        <div className="space-y-4">
          {/* Username field - only in Add mode */}
          {isAdd && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="@username"
                  value={data.username}
                  onChange={(e) => onChange(d => ({ ...d, username: e.target.value }))}
                  className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={onLookup}
                  disabled={lookingUp || !data.username}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
                >
                  {lookingUp ? 'Looking up...' : 'Lookup'}
                </button>
              </div>
            </div>
          )}

          {/* Lookup result - only in Add mode */}
          {isAdd && lookupResult && (
            <div className={`p-3 rounded-lg ${lookupResult.exists ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              {lookupResult.exists && lookupResult.user ? (
                <div className="flex items-center gap-3">
                  {lookupResult.user.profile_image_url && (
                    <img src={lookupResult.user.profile_image_url} alt="" className="w-12 h-12 rounded-full" />
                  )}
                  <div>
                    <div className="font-medium">@{lookupResult.user.username}</div>
                    <div className="text-sm text-gray-600">{lookupResult.user.name}</div>
                    <div className="text-xs text-gray-500">{lookupResult.user.followers_count?.toLocaleString()} followers</div>
                  </div>
                </div>
              ) : (
                <div className="text-red-700">{lookupResult.error || 'User not found'}</div>
              )}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Display Name{isAdd ? ' (optional)' : ''}
            </label>
            <input
              type="text"
              value={data.display_name}
              onChange={(e) => onChange(d => ({ ...d, display_name: e.target.value }))}
              placeholder={isAdd ? 'Will use Twitter name if empty' : undefined}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={data.category}
              onChange={(e) => onChange(d => ({ ...d, category: e.target.value }))}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {CATEGORIES.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Priority Tier
            </label>
            <select
              value={data.tier}
              onChange={(e) => onChange(d => ({ ...d, tier: Number(e.target.value) }))}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={1}>Tier 1 - High Priority{isAdd ? ' (check every 30 min)' : ''}</option>
              <option value={2}>Tier 2 - Medium Priority{isAdd ? ' (check every 2 hours)' : ''}</option>
              <option value={3}>Tier 3 - Low Priority{isAdd ? ' (check every 6 hours)' : ''}</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description{isAdd ? ' (optional)' : ''}
            </label>
            <textarea
              value={data.description}
              onChange={(e) => onChange(d => ({ ...d, description: e.target.value }))}
              placeholder={isAdd ? 'Brief description of this account' : undefined}
              rows={2}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id={isAdd ? 'enabled' : 'edit-enabled'}
              checked={data.enabled}
              onChange={(e) => onChange(d => ({ ...d, enabled: e.target.checked }))}
              className="w-4 h-4"
            />
            <label htmlFor={isAdd ? 'enabled' : 'edit-enabled'} className="text-sm text-gray-700">
              Enable collection for this account
            </label>
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            Cancel
          </button>
          <button
            onClick={onSubmit}
            disabled={isSubmitDisabled}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            {submitLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
