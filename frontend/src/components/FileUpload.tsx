import { useState, useRef, ChangeEvent, DragEvent } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File) => Promise<void>;
  acceptedFileTypes?: string;
  maxSizeMB?: number;
  currentFileName?: string | null;
}

export default function FileUpload({ 
  onFileSelect, 
  acceptedFileTypes = ".pdf,.txt,.doc,.docx", 
  maxSizeMB = 5,
  currentFileName = null
}: FileUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = async (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      await processFile(e.target.files[0]);
    }
  };

  const processFile = async (file: File) => {
    setError(null);
    setSuccess(false);

    // Validate type (basic check)
    // const fileType = file.name.split('.').pop()?.toLowerCase();
    // if (!acceptedFileTypes.includes(`.${fileType}`)) {
    //   setError("Invalid file type. Please upload a PDF or Text file.");
    //   return;
    // }

    // Validate size
    if (file.size > maxSizeMB * 1024 * 1024) {
      setError(`File is too large. Max size is ${maxSizeMB}MB.`);
      return;
    }

    setIsUploading(true);
    try {
      await onFileSelect(file);
      setSuccess(true);
      // Reset success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error(err);
      setError("Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="w-full">
      <div 
        onClick={() => !isUploading && fileInputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-xl p-8 transition-all cursor-pointer
          flex flex-col items-center justify-center gap-3 text-center
          ${isDragOver 
            ? 'border-primary bg-primary/10' 
            : 'border-gray-700 hover:border-gray-500 bg-[#111118] hover:bg-[#16161e]'}
          ${isUploading ? 'opacity-50 pointer-events-none' : ''}
          ${success ? 'border-green-500/50 bg-green-500/5' : ''}
        `}
      >
        <input 
          ref={fileInputRef}
          type="file" 
          accept={acceptedFileTypes}
          onChange={handleFileChange}
          className="hidden" 
        />

        {isUploading ? (
          <>
            <Loader2 className="w-10 h-10 text-primary animate-spin" />
            <p className="text-gray-400 font-medium">Uploading and analyzing...</p>
          </>
        ) : success ? (
            <>
                <div className="p-3 rounded-full bg-green-500/20 text-green-400">
                    <CheckCircle2 size={24} />
                </div>
                <div>
                    <p className="text-white font-medium">Upload Successful!</p>
                    <p className="text-sm text-gray-500 mt-1">Analyzing your resume...</p>
                </div>
            </>
        ) : (
          <>
            <div className={`p-3 rounded-full ${isDragOver ? 'bg-primary/20 text-primary' : 'bg-gray-800 text-gray-400'}`}>
              <Upload size={24} />
            </div>
            
            <div>
              <p className="text-white font-medium">Click to upload or drag and drop</p>
              <p className="text-sm text-gray-500 mt-1">PDF or Text (max {maxSizeMB}MB)</p>
            </div>
          </>
        )}
      </div>

      {error && (
        <div className="mt-3 flex items-center gap-2 text-red-400 text-sm bg-red-500/10 p-3 rounded-lg animate-fade-in">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {currentFileName && !error && !isUploading && !success && (
        <div className="mt-4 p-4 bg-gray-800/50 border border-gray-700 rounded-xl flex items-center justify-between">
            <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400">
                    <FileText size={20} />
                </div>
                <div>
                    <p className="text-sm font-medium text-white">{currentFileName}</p>
                    <p className="text-xs text-green-400 flex items-center gap-1 mt-0.5">
                        <CheckCircle2 size={10} /> Uploaded & Analyzed
                    </p>
                </div>
            </div>
        </div>
      )}
    </div>
  );
}
