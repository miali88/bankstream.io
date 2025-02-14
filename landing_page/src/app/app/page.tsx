'use client'

import React from 'react';
import { Card } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { 
  UserGroupIcon, 
  BanknotesIcon, 
  ChartBarIcon, 
  ClockIcon,
  ChevronDownIcon,
  ChevronUpIcon 
} from '@heroicons/react/24/outline'
import { useState } from 'react'
import { QRCodeSVG } from 'qrcode.react';

// Add interfaces for type safety
interface BankAccount {
  accountNumber: string;
  accountType: string;
  balance: string;
}

interface Bank {
  name: string;
  accounts: BankAccount[];
}

interface Client {
  name: string;
  banks: Bank[];
  status: 'Active' | 'Pending';
}

// Add interface for the API response
interface BuildLinkResponse {
  link: string;
}

export default function Dashboard() {
  const [expandedClient, setExpandedClient] = useState<string | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [availableAccounts, setAvailableAccounts] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedBank, setSelectedBank] = useState(null);
  const [linkUrl, setLinkUrl] = useState<string | null>(null);

  const handleAddNewAccount = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${process.env.NEXT_PUBLIC_BASE_API_URL}/gocardless/bank_list`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch available accounts');
      }
      
      const data = await response.json();
      setAvailableAccounts(data);
      setIsDialogOpen(true);
    } catch (error) {
      console.error('Error fetching available accounts:', error);
      // You might want to show an error toast here
    } finally {
      setIsLoading(false);
    }
  };

  // Update handleBankSelect to store the account details
  const handleBuildLink = async (bankId: string) => {
    try {
      setIsLoading(true);
      const response = await fetch(`${process.env.NEXT_PUBLIC_BASE_API_URL}/gocardless/build_link?institution_id=${bankId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to build link');
      }

      // The response is directly a string, not a JSON object
      const link = await response.text();
      setLinkUrl(link);
    } catch (error) {
      console.error('Error building link:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Mock data - replace with actual data from your backend
  const clients: Client[] = [
    {
      name: 'John Smith',
      banks: [
        {
          name: 'Chase Bank',
          accounts: [
            { accountNumber: '****1234', accountType: 'Checking', balance: '$24,500' },
            { accountNumber: '****5678', accountType: 'Savings', balance: '$220,500' },
          ]
        },
        {
          name: 'Bank of America',
          accounts: [
            { accountNumber: '****9012', accountType: 'Investment', balance: '$145,000' },
          ]
        }
      ],
      status: 'Active'
    },
    {
      name: 'Sarah Johnson',
      banks: [
        {
          name: 'Wells Fargo',
          accounts: [
            { accountNumber: '****3456', accountType: 'Retirement', balance: '$892,450' },
          ]
        }
      ],
      status: 'Active'
    },
    // ... other clients
  ];

  return (
    <main className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Financial Dashboard</h1>
        <p className="text-gray-500">Manage your clients and their accounts</p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="p-6">
          <div className="flex items-center">
            <UserGroupIcon className="h-12 w-12 text-blue-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Clients</p>
              <p className="text-2xl font-semibold">1,284</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <BanknotesIcon className="h-12 w-12 text-green-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Assets Under Management</p>
              <p className="text-2xl font-semibold">$842.5M</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <ChartBarIcon className="h-12 w-12 text-purple-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Active Accounts</p>
              <p className="text-2xl font-semibold">3,427</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <ClockIcon className="h-12 w-12 text-orange-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Pending Actions</p>
              <p className="text-2xl font-semibold">24</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Updated Recent Clients section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Card className="col-span-2 p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Clients</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">Client Name</th>
                  <th className="text-left py-3 px-4">Banks</th>
                  <th className="text-left py-3 px-4">Total Balance</th>
                  <th className="text-left py-3 px-4">Status</th>
                  <th className="text-left py-3 px-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                {clients.map((client, index) => (
                  <React.Fragment key={client.name + index}>
                    <tr className="border-b">
                      <td className="py-3 px-4">{client.name}</td>
                      <td className="py-3 px-4">{client.banks.length} banks</td>
                      <td className="py-3 px-4">
                        {client.banks.reduce((total, bank) => 
                          total + bank.accounts.reduce((bankTotal, account) => 
                            bankTotal + parseFloat(account.balance.replace(/[$,]/g, '')), 0), 0
                        ).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded-full text-sm ${
                          client.status === 'Active' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {client.status}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <button
                          onClick={() => setExpandedClient(expandedClient === client.name ? null : client.name)}
                          className="text-blue-500 hover:text-blue-700"
                        >
                          {expandedClient === client.name ? 
                            <ChevronUpIcon className="h-5 w-5" /> : 
                            <ChevronDownIcon className="h-5 w-5" />
                          }
                        </button>
                      </td>
                    </tr>
                    {expandedClient === client.name && (
                      <tr>
                        <td colSpan={5} className="bg-gray-50 p-4">
                          <div className="space-y-4">
                            {client.banks.map((bank, bankIndex) => (
                              <div key={bankIndex} className="border rounded-lg p-4">
                                <h3 className="font-semibold text-lg mb-2">{bank.name}</h3>
                                <table className="w-full">
                                  <thead>
                                    <tr className="text-sm text-gray-600">
                                      <th className="text-left py-2">Account Number</th>
                                      <th className="text-left py-2">Type</th>
                                      <th className="text-left py-2">Balance</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {bank.accounts.map((account, accountIndex) => (
                                      <tr key={accountIndex}>
                                        <td className="py-2">{account.accountNumber}</td>
                                        <td className="py-2">{account.accountType}</td>
                                        <td className="py-2">{account.balance}</td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Quick Actions */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-4">
            <button 
              className="w-full bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 transition-colors"
              onClick={handleAddNewAccount}
              disabled={isLoading}
            >
              {isLoading ? 'Loading...' : 'Add new account'}
            </button>
            <button className="w-full bg-white text-blue-500 border border-blue-500 py-2 px-4 rounded-lg hover:bg-blue-50 transition-colors">
              Create Account
            </button>
            <button className="w-full bg-white text-blue-500 border border-blue-500 py-2 px-4 rounded-lg hover:bg-blue-50 transition-colors">
              Generate Reports
            </button>
            <button className="w-full bg-white text-blue-500 border border-blue-500 py-2 px-4 rounded-lg hover:bg-blue-50 transition-colors">
              Schedule Meeting
            </button>
          </div>
        </Card>
      </div>

      {/* Add New Account Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {linkUrl ? 'Scan QR Code' : 'Select a Bank'}
            </DialogTitle>
          </DialogHeader>
          <div className="py-4">
            {!linkUrl ? (
              // Existing bank selection view
              availableAccounts.length > 0 ? (
                <div className="max-h-[60vh] overflow-y-auto space-y-2">
                  {availableAccounts.map((bank: any) => (
                    <div
                      key={bank.id}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        selectedBank === bank.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'hover:border-gray-400'
                      }`}
                      onClick={() => handleBuildLink(bank.id)}
                    >
                      <div className="flex items-center space-x-3">
                        {bank.logo_url && (
                          <img
                            src={bank.logo_url}
                            alt={`${bank.name} logo`}
                            className="w-8 h-8 object-contain"
                          />
                        )}
                        <div>
                          <h3 className="font-medium">{bank.name}</h3>
                          {bank.description && (
                            <p className="text-sm text-gray-500">{bank.description}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-gray-500">No available banks found</p>
              )
            ) : (
              // New QR code view
              <div className="flex flex-col items-center space-y-4 p-4">
                <QRCodeSVG value={linkUrl} size={256} />
                <p className="text-sm text-gray-500">Scan this QR code with your mobile device, or click the link below to open in your browser</p>
                <div className="flex space-x-4">
                  <button
                    onClick={() => window.open(linkUrl, '_blank')}
                    className="text-blue-500 hover:text-blue-700 text-sm"
                  >
                    Open in new tab
                  </button>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(linkUrl);
                      // Optionally add a toast notification here
                    }}
                    className="text-blue-500 hover:text-blue-700 text-sm"
                  >
                    Copy link
                  </button>
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </main>
  )
}
