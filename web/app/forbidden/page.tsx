import Link from 'next/link';
import { ShieldX, ArrowLeft, Home } from 'lucide-react';

export default function ForbiddenPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="text-center">
            <ShieldX className="mx-auto h-12 w-12 text-red-500" />
            <h1 className="mt-6 text-3xl font-extrabold text-gray-900">
              Forbidden
            </h1>
            <p className="mt-2 text-sm text-gray-600">
              You don't have the required permissions to access this resource.
            </p>
            <p className="mt-1 text-xs text-gray-500">
              If you believe this is an error, please contact support.
            </p>
          </div>

          <div className="mt-8 space-y-4">
            <button
              onClick={() => window.history.back()}
              className="w-full flex justify-center items-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go Back
            </button>

            <Link
              href="/dashboard"
              className="w-full flex justify-center items-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500"
            >
              <Home className="w-4 h-4 mr-2" />
              Dashboard
            </Link>
          </div>

          <div className="mt-6 text-center">
            <p className="text-xs text-gray-500">
              Error Code: 403 - Forbidden
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}