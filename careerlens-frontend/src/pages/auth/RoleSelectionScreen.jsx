import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, GraduationCap, Building2, Check } from 'lucide-react';
import Auth3DBackground from '../../components/auth/Auth3DBackground';
import Logo from '../../components/Logo';

const RoleSelectionScreen = () => {
  const navigate = useNavigate();
  const [selectedRole, setSelectedRole] = useState(null);

  const handleContinue = () => {
    if (selectedRole) {
      navigate(`/register?role=${selectedRole}`);
    }
  };

  const roles = [
    {
      id: 'student',
      title: 'Student',
      description: 'Analyze resumes & discover career opportunities',
      benefits: ['Resume Analysis', 'Skill Assessment', 'Career Roadmap', 'Job Recommendations'],
      icon: GraduationCap,
      gradient: 'linear-gradient(135deg, #00C2CB, #0ea5e9)',
      glowColor: 'rgba(0, 194, 203, 0.15)',
      accentColor: '#00C2CB',
    },
    {
      id: 'recruiter',
      title: 'Recruiter',
      description: 'Batch analyze candidates & find top talent',
      benefits: ['Batch Upload', 'Candidate Ranking', 'Quick Screening', 'Skill Matching'],
      icon: Building2,
      gradient: 'linear-gradient(135deg, #10B981, #14B8A6)',
      glowColor: 'rgba(16, 185, 129, 0.15)',
      accentColor: '#10B981',
    },
  ];

  return (
    <Auth3DBackground>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        className="w-full max-w-4xl py-12"
      >
        {/* Header with Logo */}
        <div className="text-center mb-12">
          {/* Logo Presentation */}
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1, duration: 0.7, type: 'spring', stiffness: 80 }}
            className="flex justify-center mb-6"
          >
            <div 
              className="bg-white rounded-full p-8 flex items-center justify-center"
              style={{
                boxShadow: '0 15px 40px rgba(0, 194, 203, 0.15), 0 5px 15px rgba(15, 23, 42, 0.05)',
                border: '1px solid rgba(0, 194, 203, 0.1)'
              }}
            >
              <Logo size="lg" />
            </div>
          </motion.div>

          {/* Tagline */}
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-slate-500 font-medium text-lg"
          >
            Choose your path and get started
          </motion.p>
        </div>

        {/* Role Cards */}
        <div className="grid md:grid-cols-2 gap-6 mb-10">
          {roles.map((role, idx) => {
            const isSelected = selectedRole === role.id;
            const IconComponent = role.icon;

            return (
              <motion.div
                key={role.id}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + idx * 0.15, type: 'spring', stiffness: 100, damping: 15 }}
                onClick={() => setSelectedRole(role.id)}
                whileHover={{ y: -6, transition: { duration: 0.2 } }}
                className="cursor-pointer"
              >
                <motion.div
                  className="relative rounded-2xl p-[1px] overflow-hidden transition-all duration-500"
                  style={{
                    background: isSelected
                      ? role.gradient
                      : 'linear-gradient(135deg, rgba(203, 213, 225, 0.8), rgba(241, 245, 249, 0.4))',
                  }}
                  animate={{
                    boxShadow: isSelected
                      ? `0 25px 50px ${role.glowColor}, 0 0 0 1px ${role.accentColor}40`
                      : '0 10px 30px rgba(15,23,42,0.05)',
                  }}
                >
                  <div
                    className="rounded-2xl p-8 relative"
                    style={{
                      background: isSelected
                        ? 'rgba(255, 255, 255, 0.95)'
                        : 'rgba(255, 255, 255, 0.8)',
                      backdropFilter: 'blur(30px)',
                    }}
                  >
                    {/* Gradient bar */}
                    <div
                      className="absolute top-0 left-0 right-0 h-[3px] transition-opacity duration-300"
                      style={{
                        background: role.gradient,
                        opacity: isSelected ? 1 : 0.2,
                      }}
                    />

                    {/* Icon */}
                    <motion.div
                      className="w-14 h-14 rounded-xl mb-6 flex items-center justify-center"
                      style={{
                        background: isSelected ? `${role.accentColor}1A` : 'rgba(241, 245, 249, 1)',
                        border: `1px solid ${isSelected ? `${role.accentColor}30` : 'rgba(203, 213, 225, 0.5)'}`,
                        boxShadow: isSelected ? `0 0 30px ${role.accentColor}20` : 'none',
                      }}
                      animate={isSelected ? { scale: [1, 1.05, 1] } : { scale: 1 }}
                      transition={{ duration: 2, repeat: Infinity }}
                    >
                      <IconComponent
                        size={26}
                        style={{ color: isSelected ? role.accentColor : '#64748b' }}
                      />
                    </motion.div>

                    {/* Title */}
                    <h2
                      className="text-2xl font-bold mb-2"
                      style={{ color: isSelected ? role.accentColor : '#0f172a' }}
                    >
                      {role.title}
                    </h2>

                    {/* Description */}
                    <p className="text-slate-500 font-medium text-sm mb-6">
                      {role.description}
                    </p>

                    {/* Benefits */}
                    <ul className="space-y-3 mb-2">
                      {role.benefits.map((benefit, i) => (
                        <motion.li
                          key={i}
                          className="flex items-center text-sm font-medium"
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.4 + idx * 0.1 + i * 0.05 }}
                        >
                          <span
                            className="w-2 h-2 rounded-full mr-3 flex-shrink-0"
                            style={{ background: isSelected ? role.accentColor : '#cbd5e1' }}
                          />
                          <span className={isSelected ? 'text-slate-700' : 'text-slate-500'}>
                            {benefit}
                          </span>
                        </motion.li>
                      ))}
                    </ul>

                    {/* Selected Check */}
                    {isSelected && (
                      <motion.div
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="absolute top-6 right-6 w-8 h-8 rounded-full flex items-center justify-center"
                        style={{
                          background: role.gradient,
                          boxShadow: `0 5px 15px ${role.glowColor}`,
                        }}
                      >
                        <Check size={16} className="text-white" strokeWidth={3} />
                      </motion.div>
                    )}
                  </div>
                </motion.div>
              </motion.div>
            );
          })}
        </div>

        {/* Continue Button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="max-w-md mx-auto"
        >
          <motion.button
            onClick={handleContinue}
            disabled={!selectedRole}
            whileHover={selectedRole ? { scale: 1.01, y: -2 } : {}}
            whileTap={selectedRole ? { scale: 0.98 } : {}}
            className={`auth-btn-shimmer w-full py-4 px-6 rounded-xl font-bold flex items-center justify-center gap-2 transition-all duration-300 cursor-pointer ${
              !selectedRole ? 'opacity-40 cursor-not-allowed' : ''
            }`}
            style={{
              background: selectedRole
                ? 'linear-gradient(135deg, #00C2CB 0%, #0ea5e9 100%)'
                : 'rgba(203, 213, 225, 0.4)',
              color: selectedRole ? 'white' : '#64748b',
              border: selectedRole ? 'none' : '1px solid rgba(203, 213, 225, 0.8)',
              boxShadow: selectedRole
                ? '0 10px 30px rgba(0, 194, 203, 0.3), 0 4px 10px rgba(15, 23, 42, 0.1)'
                : 'none',
            }}
          >
            Continue as {selectedRole ? (selectedRole === 'student' ? 'Student' : 'Recruiter') : '...'}
            <ArrowRight size={18} />
          </motion.button>
        </motion.div>

        {/* Login Link */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="text-center font-medium text-slate-500 mt-8"
        >
          Already have an account?{' '}
          <button
            onClick={() => navigate('/login')}
            className="text-cyan-600 hover:text-cyan-500 font-bold transition-colors cursor-pointer"
          >
            Sign in
          </button>
        </motion.p>
      </motion.div>
    </Auth3DBackground>
  );
};

export default RoleSelectionScreen;
