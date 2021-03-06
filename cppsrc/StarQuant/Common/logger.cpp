#include <Common/logger.h>
#include <Common/util.h>
#include <Common/config.h>
// #include <Common/datastruct.h>

#include <log4cplus/initializer.h>
#include <log4cplus/configurator.h>
#include <log4cplus/fileappender.h>
#include <log4cplus/consoleappender.h>
#include <log4cplus/loglevel.h>
#include <fstream>
#include <boost/program_options.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/ini_parser.hpp>
#include <boost/filesystem.hpp>
#include <boost/algorithm/string.hpp>



#ifdef _WIN32
#include <nanomsg/src/nn.h>
#include <nanomsg/src/pubsub.h>
#else
#include <nanomsg/nn.h>
#include <nanomsg/pubsub.h>
#endif

#include <boost/filesystem.hpp>

namespace fs = boost::filesystem;
using std::lock_guard;
using namespace log4cplus;

namespace StarQuant
{
	logger* logger::pinstance_ = nullptr;
	mutex logger::instancelock_;

	logger::logger() : logfile(nullptr) {
		Initialize();
	}

	logger::~logger() {
		fclose(logfile);
	}

	logger& logger::instance() {
		if (pinstance_ == nullptr) {
			lock_guard<mutex> g(instancelock_);
			if (pinstance_ == nullptr) {
				pinstance_ = new logger();
			}
		}
		return *pinstance_;
	}

	void logger::Initialize() {
		string fname;



		if (CConfig::instance()._mode == RUN_MODE::REPLAY_MODE) {
			fname = CConfig::instance().logDir() + "/starequant-replay-" + ymd() + ".txt";
		}
		else {
			fname = CConfig::instance().logDir() + "/starquant-" + ymd() + ".txt";
		}

		logfile = fopen(fname.c_str(), "w");
		setvbuf(logfile, nullptr, _IONBF, 0);
	}

	void logger::Printf2File(const char *format, ...) {
		lock_guard<mutex> g(instancelock_);

		static char buf[1024 * 2];
		string tmp = nowMS();
		size_t sz = tmp.size();
		strcpy(buf, tmp.c_str());
		buf[sz] = ' ';

		va_list args;
		va_start(args, format);
		vsnprintf(buf + sz + 1, 1024 * 2 - sz - 1, format, args);
		size_t buflen = strlen(buf);
		fwrite(buf, sizeof(char), buflen, logfile);
		va_end(args);
	}

	static bool configured = false;

	bool SQLogger::doConfigure(string configureName)
	{
		if (!configured)
		{
			log4cplus::PropertyConfigurator::doConfigure(LOG4CPLUS_TEXT(configureName));
			configured = true;
			return true;
		}
		else
		{
			return false;
		}
	}

	std::shared_ptr<SQLogger> SQLogger::getLogger(string name)
	{
		return std::shared_ptr<SQLogger>(new SQLogger(name));
	}

	SQLogger::SQLogger(string name)
	{
		doConfigure(CConfig::instance().logconfigfile_);
		logger = log4cplus::Logger::getInstance(name);
	}

	string SQLogger::getConfigFolder()
	{
		return CConfig::instance().configDir();
	}



}
