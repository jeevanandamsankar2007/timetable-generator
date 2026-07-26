import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, Printer } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { api } from '../lib/api';
import { useToast } from '../contexts/ToastContext';
import './TimetableView.css';

const TimetableView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [defaultFormat, setDefaultFormat] = useState(localStorage.getItem('exportFormat') || 'pdf');

  useEffect(() => {
    fetchTimetable();
  }, [id]);

  useEffect(() => {
    const handleFormatChange = () => setDefaultFormat(localStorage.getItem('exportFormat') || 'pdf');
    window.addEventListener('exportformatchange', handleFormatChange);
    return () => window.removeEventListener('exportformatchange', handleFormatChange);
  }, []);

  const fetchTimetable = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/faculty/${id}/timetable`);
      setData(res);
    } catch (error) {
      addToast('Failed to load timetable: ' + error.message, 'error');
      navigate(-1);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (format) => {
    try {
      addToast(`Generating ${format.toUpperCase()}...`, 'info');
      const filename = `timetable_${data.faculty_name.replace(/\s+/g, '_')}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      await api.download(`/download/${format}/${id}`, filename);
      addToast('Download complete', 'success');
    } catch (error) {
      addToast(`Failed to download ${format}: ` + error.message, 'error');
    }
  };

  if (loading) {
    return (
      <div className="timetable-page flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!data) return null;

  // Extract unique subjects from schedule
  const uniqueSubjects = new Set();
  data.schedule.forEach(row => {
    row.forEach(cell => {
      if (cell.type === 'class' && cell.subject) {
        uniqueSubjects.add(`${cell.subject_code ? cell.subject_code + '-' : ''}${cell.subject}`);
      }
    });
  });
  const subjectText = Array.from(uniqueSubjects).join(', ') || '-';

  // Helper for Roman numerals
  const romanize = (num) => {
    const roman = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"];
    return roman[num] || num;
  };

  let periodCounter = 1;

  return (
    <div className="timetable-page print-container">
      <div className="no-print flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button className="back-btn" onClick={() => navigate(-1)}>
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="page-title">{data.faculty_name}'s Timetable</h1>
            <p className="page-subtitle">{data.department || 'General'} • Generated automatically</p>
          </div>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" icon={Printer} onClick={() => window.print()}>Print</Button>
          {defaultFormat === 'xlsx' ? (
            <>
              <Button variant="outline" icon={Download} onClick={() => handleDownload('pdf')}>PDF</Button>
              <Button variant="primary" icon={Download} onClick={() => handleDownload('excel')}>Excel</Button>
            </>
          ) : (
            <>
              <Button variant="outline" icon={Download} onClick={() => handleDownload('excel')}>Excel</Button>
              <Button variant="primary" icon={Download} onClick={() => handleDownload('pdf')}>PDF</Button>
            </>
          )}
        </div>
      </div>

      {/* Print Template Container */}
      <div className="print-template">
        <div className="template-header text-center font-bold mb-4">
          <h2 className="college-name">P.S.N.A. COLLEGE OF ENGINEERING & TECHNOLOGY, DINDIGUL – 624 622</h2>
          <h3 className="timetable-title mt-2 mb-4 underline">FACULTY TIME TABLE</h3>
        </div>

        <div className="faculty-details-grid mb-6">
          <div className="detail-row">
            <span className="detail-label">Name</span>
            <span className="detail-colon">:</span>
            <span className="detail-value font-bold">{data.faculty_name}</span>
            <span className="detail-label ml-8">Department</span>
            <span className="detail-colon">:</span>
            <span className="detail-value font-bold"></span>
          </div>
          <div className="detail-row mt-2">
            <span className="detail-label">Subject</span>
            <span className="detail-colon">:</span>
            <span className="detail-value font-bold">{subjectText}</span>
            <span className="detail-label ml-8">Academic Year</span>
            <span className="detail-colon">:</span>
            <span className="detail-value font-bold"></span>
          </div>
          <div className="detail-row mt-2">
            <span className="detail-label"></span>
            <span className="detail-colon"></span>
            <span className="detail-value"></span>
            <span className="detail-label ml-8">Semester</span>
            <span className="detail-colon">:</span>
            <span className="detail-value font-bold"></span>
          </div>
        </div>

        <div className="timetable-container border-2 border-black">
          <table className="timetable template-table w-full">
            <thead>
              <tr>
                <th className="day-hour-header">DAY /<br/>HOUR</th>
                {data.headers.map((header, idx) => {
                  const isBreak = header.toLowerCase().includes('break') || header.toLowerCase().includes('lunch');
                  const roman = isBreak ? '' : romanize(periodCounter++);
                  return (
                    <th key={idx}>
                      <div className="font-bold text-lg mb-1">{roman}</div>
                      <div className="whitespace-pre-line text-sm">{header}</div>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {data.days.map((day, rowIdx) => (
                <tr key={rowIdx}>
                  <td className="day-cell font-bold uppercase">{day.substring(0, 3)}</td>
                  {data.schedule[rowIdx].map((cell, colIdx) => {
                    const isBreakCell = cell.type === 'break' || cell.type === 'lunch';
                    
                    if (isBreakCell) {
                      if (rowIdx === 0) {
                        return (
                          <td key={colIdx} rowSpan={data.days.length} className="period-cell break-cell border-black">
                            <div className="vertical-text font-bold">
                              {cell.label || data.headers[colIdx] || 'BREAK'}
                            </div>
                          </td>
                        );
                      } else {
                        return null; // Skip rendering since rowspan handles it
                      }
                    }

                    return (
                      <td key={colIdx} className={`period-cell type-${cell.type} border-black`}>
                        {cell.type === 'class' && (
                          <div className="class-content">
                            <span className="subject">{cell.subject_code || cell.subject}</span>
                          </div>
                        )}
                        {cell.type === 'free' && <span className="free-dash"></span>}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="template-footer mt-12 flex justify-between font-bold">
          <div>DEPT TT I/C</div>
          <div>HOD-{data.department || 'IT'}</div>
          <div>Prof. TT I/C</div>
        </div>
      </div>
    </div>
  );
};

export default TimetableView;
