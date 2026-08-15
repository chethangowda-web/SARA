import { useNavigate } from 'react-router-dom';
import AppLayout from '../../layouts/AppLayout';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import SubmitGrievanceWizard from '../../components/grievances/SubmitGrievanceWizard';
import { FilePlus } from 'lucide-react';

export function CitizenSubmitPage() {
  const navigate = useNavigate();

  return (
    <AppLayout title="Submit Grievance" breadcrumb="Citizen Workspace">
      <div className="space-y-6 max-w-4xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>
              <FilePlus className="w-5 h-5 text-blue-400" />
              Grievance Submission Wizard
            </CardTitle>
          </CardHeader>
          <CardContent>
            <SubmitGrievanceWizard
              onClose={() => {
                navigate('/citizen/grievances');
              }}
            />
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}

export default CitizenSubmitPage;
