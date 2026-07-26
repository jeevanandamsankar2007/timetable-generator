import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, BookOpen, Clock, FileText, LayoutGrid } from 'lucide-react';
import Card from '../components/ui/Card';
import { api } from '../lib/api';
import './FacultySearch.css';

const FacultySearch = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [facultyList, setFacultyList] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchFaculty();
  }, []);

  const fetchFaculty = async () => {
    try {
      setLoading(true);
      const data = await api.get('/faculty?per_page=1000');
      setFacultyList(data.items || []);
    } catch (error) {
      console.error('Failed to fetch faculty:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredFaculty = facultyList.filter(faculty => 
    faculty.faculty_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCardClick = (id) => {
    navigate(`/faculty/${id}`);
  };

  return (
    <div className="faculty-search-page">
      <div className="dashboard-header text-center mb-8">
        <h1 className="page-title">Faculty Search</h1>
        <p className="page-subtitle">Find and view individual faculty timetables.</p>
      </div>

      <div className="search-container mb-8">
        <div className="search-input-wrapper relative">
          <Search className="search-icon-large" size={24} />
          <input 
            type="text" 
            className="search-input-large" 
            placeholder="Search Faculty Name..." 
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setShowDropdown(true);
            }}
            onFocus={() => setShowDropdown(true)}
            onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
          />
          
          {showDropdown && searchTerm && filteredFaculty.length > 0 && (
            <ul className="autocomplete-dropdown">
              {filteredFaculty.slice(0, 8).map((faculty) => (
                <li 
                  key={faculty.id} 
                  className="autocomplete-item"
                  onMouseDown={() => handleCardClick(faculty.id)}
                >
                  <div className="autocomplete-name">{faculty.faculty_name}</div>
                  {faculty.department && <div className="autocomplete-dept">{faculty.department}</div>}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : filteredFaculty.length > 0 ? (
        <div className="faculty-grid">
          {filteredFaculty.map(faculty => (
            <Card key={faculty.id} hover padding="md" className="faculty-card cursor-pointer" onClick={() => handleCardClick(faculty.id)}>
              <div className="faculty-card-header border-b">
                <h3 className="faculty-name">{faculty.faculty_name}</h3>
                {faculty.department && <p className="text-sm text-secondary">{faculty.department}</p>}
              </div>
              <div className="faculty-stats">
                <div className="stat-item">
                  <LayoutGrid size={16} className="stat-icon" />
                  <span className="stat-text">{faculty.total_classes || 0} Classes</span>
                </div>
                <div className="stat-item">
                  <BookOpen size={16} className="stat-icon" />
                  <span className="stat-text">{faculty.total_subjects || 0} Subjects</span>
                </div>
                <div className="stat-item">
                  <Clock size={16} className="stat-icon" />
                  <span className="stat-text">{faculty.total_hours || 0} Hours/Week</span>
                </div>
                <div className="stat-item">
                  <FileText size={16} className="stat-icon" />
                  <span className="stat-text">1 Timetable</span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-icon-wrapper">
            <Search size={48} className="text-tertiary" />
          </div>
          <h3 className="empty-title">No Faculty Found</h3>
          <p className="empty-desc">We couldn't find any faculty matching "{searchTerm}".</p>
        </div>
      )}
    </div>
  );
};

export default FacultySearch;
