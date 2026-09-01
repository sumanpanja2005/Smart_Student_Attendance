/**
 * Utility formatting functions
 */

export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export const formatPercentage = (value) => {
  if (value === undefined || value === null) return '0%';
  return `${Math.round(value)}%`;
};
