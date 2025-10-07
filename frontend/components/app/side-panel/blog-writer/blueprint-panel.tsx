'use client';

import { motion, AnimatePresence } from "framer-motion";
import React, { useState, useEffect } from "react";
import { useFetchAIRecommendations } from "@/stores/use-user-store"; // adjust path
 
interface BlueprintPanelProps {
  urlId: string;
  isOpen?: boolean; // optional for backward compatibility
  onClose: () => void;
  onSave: (blueprints: any[]) => void;
  title?: string;
  hasUnsavedChanges?: boolean;
}

export const BlueprintPanel: React.FC<BlueprintPanelProps> = ({
  urlId,
  isOpen: isOpenProp,
  onClose,
  onSave,
  title = "Blueprint",
  hasUnsavedChanges = false,
}) => {
  const fetchAIRecommendations = useFetchAIRecommendations();
const [blueprints, setBlueprints] = useState<any[]>([
  { id: "1", title: "Sample Blueprint 1", description: "This is a test blueprint." },
  { id: "2", title: "Sample Blueprint 2", description: "Another test blueprint." },
]);

const [editedBlueprints, setEditedBlueprints] = useState([...blueprints]);

  const [loading, setLoading] = useState(false);

  // Use prop if provided, otherwise default to true for testing
  const [isOpen, setIsOpen] = useState(isOpenProp ?? true);

  // Fetch blueprints when panel opens
  useEffect(() => {
    if (!isOpen) return;

    const loadBlueprints = async () => {
      setLoading(true);
      try {
        const recs = await fetchAIRecommendations(urlId);
        const blueprintItems = recs.filter((r) => r.type === "seo_blueprint");
        setBlueprints(blueprintItems);
        setEditedBlueprints([...blueprintItems]); // initialize editable copy
      } catch (err) {
        console.error("Failed to fetch blueprints", err);
        setBlueprints([]);
        setEditedBlueprints([]);
      } finally {
        setLoading(false);
      }
    };

    loadBlueprints();
  }, [isOpen, fetchAIRecommendations, urlId]);

  const handleClose = () => {
    if (hasUnsavedChanges && !confirm("Unsaved changes will be lost. Are you sure?")) return;
    setIsOpen(false); // close internally
    onClose?.();
  };

  const handleEdit = (idx: number, field: "title" | "description", value: string) => {
    const newBlueprints = [...editedBlueprints];
    newBlueprints[idx] = { ...newBlueprints[idx], [field]: value };
    setEditedBlueprints(newBlueprints);
  };

  const handleSave = () => {
    onSave(editedBlueprints);
    handleClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
          onClick={handleClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="bg-gray-900 rounded-lg w-full max-w-3xl max-h-screen overflow-hidden flex flex-col shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex justify-between items-center p-6 border-b border-gray-800">
              <h2 className="text-xl font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
                {title}
              </h2>
              <button
                onClick={handleClose}
                className="text-gray-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Body */}
            <div className="flex-1 p-6 overflow-y-auto space-y-4">
              {loading ? (
                <p className="text-gray-400">Loading blueprints...</p>
              ) : blueprints.length === 0 ? (
                <p className="text-gray-400">No blueprints available.</p>
              ) : (
                editedBlueprints.map((bp, idx) => (
                  <div
                    key={bp.id || idx}
                    className="p-3 border border-gray-700 rounded flex flex-col gap-2"
                  >
                    <input
                      type="text"
                      value={bp.title}
                      onChange={(e) => handleEdit(idx, "title", e.target.value)}
                      className="w-full text-white bg-gray-800 p-1 rounded"
                      placeholder="Blueprint title"
                    />
                    <textarea
                      value={bp.description}
                      onChange={(e) => handleEdit(idx, "description", e.target.value)}
                      className="w-full text-gray-400 bg-gray-800 p-1 rounded resize-none"
                      placeholder="Blueprint description"
                    />
                  </div>
                ))
              )}
            </div>

            {/* Footer */}
            <div className="flex justify-end p-6 border-t border-gray-800">
              <button
                onClick={handleClose}
                className="px-4 py-2 rounded-md border border-gray-600 text-white mr-3"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="bg-gradient-to-r from-yellow-400 to-orange-500 text-black px-4 py-2 rounded-md font-bold"
              >
                Save Changes
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
